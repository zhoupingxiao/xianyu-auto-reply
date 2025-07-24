from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Tuple, Optional, Dict
from pathlib import Path
from urllib.parse import unquote
import hashlib
import secrets
import time
import json
import os
import uvicorn

import cookie_manager
from db_manager import db_manager
from file_log_collector import setup_file_logging, get_file_log_collector
from ai_reply_engine import ai_reply_engine

# 关键字文件路径
KEYWORDS_FILE = Path(__file__).parent / "回复关键字.txt"

# 简单的用户认证配置
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()  # 默认密码: admin123
SESSION_TOKENS = {}  # 存储会话token
TOKEN_EXPIRE_TIME = 24 * 60 * 60  # token过期时间：24小时

# HTTP Bearer认证
security = HTTPBearer(auto_error=False)


def load_keywords() -> List[Tuple[str, str]]:
    """读取关键字→回复映射表

    文件格式支持：
        关键字<空格/制表符/冒号>回复内容
    忽略空行和以 # 开头的注释行
    """
    mapping: List[Tuple[str, str]] = []
    if not KEYWORDS_FILE.exists():
        return mapping

    with KEYWORDS_FILE.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # 尝试用\t、空格、冒号分隔
            if '\t' in line:
                key, reply = line.split('\t', 1)
            elif ' ' in line:
                key, reply = line.split(' ', 1)
            elif ':' in line:
                key, reply = line.split(':', 1)
            else:
                # 无法解析的行，跳过
                continue
            mapping.append((key.strip(), reply.strip()))
    return mapping


KEYWORDS_MAPPING = load_keywords()


# 认证相关模型
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    message: str


def generate_token() -> str:
    """生成随机token"""
    return secrets.token_urlsafe(32)


def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> bool:
    """验证token"""
    if not credentials:
        return False

    token = credentials.credentials
    if token not in SESSION_TOKENS:
        return False

    # 检查token是否过期
    if time.time() - SESSION_TOKENS[token] > TOKEN_EXPIRE_TIME:
        del SESSION_TOKENS[token]
        return False

    return True


def require_auth(authenticated: bool = Depends(verify_token)):
    """需要认证的依赖"""
    if not authenticated:
        raise HTTPException(status_code=401, detail="未授权访问")


def match_reply(cookie_id: str, message: str) -> Optional[str]:
    """根据 cookie_id 及消息内容匹配回复
    只有启用的账号才会匹配关键字回复
    """
    mgr = cookie_manager.manager
    if mgr is None:
        return None

    # 检查账号是否启用
    if not mgr.get_cookie_status(cookie_id):
        return None  # 禁用的账号不参与自动回复

    # 优先账号级关键字
    if mgr.get_keywords(cookie_id):
        for k, r in mgr.get_keywords(cookie_id):
            if k in message:
                return r

    # 全局关键字
    for k, r in KEYWORDS_MAPPING:
        if k in message:
            return r
    return None


class RequestModel(BaseModel):
    cookie_id: str
    msg_time: str
    user_url: str
    send_user_id: str
    send_user_name: str
    item_id: str
    send_message: str
    chat_id: str


class ResponseData(BaseModel):
    send_msg: str


class ResponseModel(BaseModel):
    code: int
    data: ResponseData


app = FastAPI(
    title="Xianyu Auto Reply API",
    version="1.0.0",
    description="闲鱼自动回复系统API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置统一的日志系统
import time
from loguru import logger

# 确保日志目录存在
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, f"xianyu_{time.strftime('%Y-%m-%d')}.log")

# 移除默认的日志处理器
logger.remove()

# 导入日志过滤器
try:
    from log_filter import filter_log_record
except ImportError:
    # 如果过滤器不可用，使用默认过滤器
    def filter_log_record(record):
        return True

# 添加文件日志处理器，使用与XianyuAutoAsync相同的格式，并应用过滤器
logger.add(
    log_path,
    rotation="1 day",
    retention="7 days",
    compression="zip",
    level="INFO",
    format='{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} - {message}',
    encoding='utf-8',
    enqueue=False,  # 立即写入
    buffering=1,    # 行缓冲
    filter=filter_log_record  # 应用日志过滤器
)

# 初始化文件日志收集器
setup_file_logging()

# 添加一条测试日志
logger.info("Web服务器启动，统一日志系统已初始化")

# 不需要记录到文件的API路径
EXCLUDED_LOG_PATHS = {
    '/logs',
    '/logs/stats',
    '/logs/clear',
    '/health',
    '/docs',
    '/redoc',
    '/openapi.json',
    '/favicon.ico'
}

# 不需要记录的路径前缀
EXCLUDED_LOG_PREFIXES = {
    '/static/',
    '/docs',
    '/redoc'
}

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()

    # 检查是否需要记录日志
    should_log = (
        request.url.path not in EXCLUDED_LOG_PATHS and
        not any(request.url.path.startswith(prefix) for prefix in EXCLUDED_LOG_PREFIXES)
    )

    if should_log:
        logger.info(f"🌐 API请求: {request.method} {request.url.path}")

    response = await call_next(request)

    if should_log:
        process_time = time.time() - start_time
        logger.info(f"✅ API响应: {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")

    return response

# 提供前端静态文件
import os
static_dir = os.path.join(os.path.dirname(__file__), 'static')
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount('/static', StaticFiles(directory=static_dir), name='static')


# 健康检查端点
@app.get('/health')
async def health_check():
    """健康检查端点，用于Docker健康检查和负载均衡器"""
    try:
        # 检查Cookie管理器状态
        manager_status = "ok" if cookie_manager.manager is not None else "error"

        # 检查数据库连接
        from db_manager import db_manager
        try:
            db_manager.get_all_cookies()
            db_status = "ok"
        except Exception:
            db_status = "error"

        # 获取系统状态
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()

        status = {
            "status": "healthy" if manager_status == "ok" and db_status == "ok" else "unhealthy",
            "timestamp": time.time(),
            "services": {
                "cookie_manager": manager_status,
                "database": db_status
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_info.percent,
                "memory_available": memory_info.available
            }
        }

        if status["status"] == "unhealthy":
            raise HTTPException(status_code=503, detail=status)

        return status

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e)
        }


# 重定向根路径到登录页面
@app.get('/', response_class=HTMLResponse)
async def root():
    login_path = os.path.join(static_dir, 'login.html')
    if os.path.exists(login_path):
        with open(login_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(f.read())
    else:
        return HTMLResponse('<h3>Login page not found</h3>')


# 登录页面路由
@app.get('/login.html', response_class=HTMLResponse)
async def login_page():
    login_path = os.path.join(static_dir, 'login.html')
    if os.path.exists(login_path):
        with open(login_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(f.read())
    else:
        return HTMLResponse('<h3>Login page not found</h3>')


# 管理页面（不需要服务器端认证，由前端JavaScript处理）
@app.get('/admin', response_class=HTMLResponse)
async def admin_page():
    index_path = os.path.join(static_dir, 'index.html')
    if not os.path.exists(index_path):
        return HTMLResponse('<h3>No front-end found</h3>')
    with open(index_path, 'r', encoding='utf-8') as f:
        return HTMLResponse(f.read())


# 登录接口
@app.post('/login')
async def login(request: LoginRequest):
    from db_manager import db_manager

    # 验证用户名和密码
    if request.username == ADMIN_USERNAME and db_manager.verify_admin_password(request.password):
        # 生成token
        token = generate_token()
        SESSION_TOKENS[token] = time.time()

        return LoginResponse(
            success=True,
            token=token,
            message="登录成功"
        )
    else:
        return LoginResponse(
            success=False,
            message="用户名或密码错误"
        )


# 验证token接口
@app.get('/verify')
async def verify(authenticated: bool = Depends(verify_token)):
    return {"authenticated": authenticated}


# 登出接口
@app.post('/logout')
async def logout(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if credentials and credentials.credentials in SESSION_TOKENS:
        del SESSION_TOKENS[credentials.credentials]
    return {"message": "已登出"}


@app.post("/xianyu/reply", response_model=ResponseModel)
async def xianyu_reply(req: RequestModel):
    msg_template = match_reply(req.cookie_id, req.send_message)
    if not msg_template:
        # 从数据库获取默认回复
        from db_manager import db_manager
        default_reply_settings = db_manager.get_default_reply(req.cookie_id)

        if default_reply_settings and default_reply_settings.get('enabled', False):
            msg_template = default_reply_settings.get('reply_content', '')

        # 如果数据库中没有设置或为空，返回错误
        if not msg_template:
            raise HTTPException(status_code=404, detail="未找到匹配的回复规则且未设置默认回复")

    # 按占位符格式化
    try:
        send_msg = msg_template.format(
            send_user_id=req.send_user_id,
            send_user_name=req.send_user_name,
            send_message=req.send_message,
        )
    except Exception:
        # 如果格式化失败，返回原始内容
        send_msg = msg_template

    return {"code": 200, "data": {"send_msg": send_msg}}

# ------------------------- 账号 / 关键字管理接口 -------------------------


class CookieIn(BaseModel):
    id: str
    value: str


class CookieStatusIn(BaseModel):
    enabled: bool


class DefaultReplyIn(BaseModel):
    enabled: bool
    reply_content: Optional[str] = None


class NotificationChannelIn(BaseModel):
    name: str
    type: str = "qq"
    config: str


class NotificationChannelUpdate(BaseModel):
    name: str
    config: str
    enabled: bool = True


class MessageNotificationIn(BaseModel):
    channel_id: int
    enabled: bool = True


class SystemSettingIn(BaseModel):
    key: str
    value: str
    description: Optional[str] = None


class PasswordUpdateIn(BaseModel):
    current_password: str
    new_password: str


@app.get("/cookies")
def list_cookies(_: None = Depends(require_auth)):
    if cookie_manager.manager is None:
        return []
    return cookie_manager.manager.list_cookies()


@app.get("/cookies/details")
def get_cookies_details(_: None = Depends(require_auth)):
    """获取所有Cookie的详细信息（包括值和状态）"""
    if cookie_manager.manager is None:
        return []

    result = []
    for cookie_id in cookie_manager.manager.list_cookies():
        cookie_value = cookie_manager.manager.cookies.get(cookie_id, '')
        cookie_enabled = cookie_manager.manager.get_cookie_status(cookie_id)
        result.append({
            'id': cookie_id,
            'value': cookie_value,
            'enabled': cookie_enabled
        })
    return result


@app.post("/cookies")
def add_cookie(item: CookieIn, _: None = Depends(require_auth)):
    if cookie_manager.manager is None:
        raise HTTPException(status_code=500, detail="CookieManager 未就绪")
    try:
        cookie_manager.manager.add_cookie(item.id, item.value)
        return {"msg": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put('/cookies/{cid}')
def update_cookie(cid: str, item: CookieIn, _: None = Depends(require_auth)):
    if cookie_manager.manager is None:
        raise HTTPException(status_code=500, detail='CookieManager 未就绪')
    try:
        cookie_manager.manager.update_cookie(cid, item.value)
        return {'msg': 'updated'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put('/cookies/{cid}/status')
def update_cookie_status(cid: str, status_data: CookieStatusIn, _: None = Depends(require_auth)):
    """更新账号的启用/禁用状态"""
    if cookie_manager.manager is None:
        raise HTTPException(status_code=500, detail='CookieManager 未就绪')
    try:
        cookie_manager.manager.update_cookie_status(cid, status_data.enabled)
        return {'msg': 'status updated', 'enabled': status_data.enabled}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------------- 默认回复管理接口 -------------------------

@app.get('/default-replies/{cid}')
def get_default_reply(cid: str, _: None = Depends(require_auth)):
    """获取指定账号的默认回复设置"""
    from db_manager import db_manager
    try:
        result = db_manager.get_default_reply(cid)
        if result is None:
            # 如果没有设置，返回默认值
            return {'enabled': False, 'reply_content': ''}
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put('/default-replies/{cid}')
def update_default_reply(cid: str, reply_data: DefaultReplyIn, _: None = Depends(require_auth)):
    """更新指定账号的默认回复设置"""
    from db_manager import db_manager
    try:
        # 检查数据库中是否存在该账号
        all_cookies = db_manager.get_all_cookies()
        if cid not in all_cookies:
            raise HTTPException(status_code=404, detail='账号不存在')

        db_manager.save_default_reply(cid, reply_data.enabled, reply_data.reply_content)
        return {'msg': 'default reply updated', 'enabled': reply_data.enabled}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/default-replies')
def get_all_default_replies(_: None = Depends(require_auth)):
    """获取所有账号的默认回复设置"""
    from db_manager import db_manager
    try:
        return db_manager.get_all_default_replies()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete('/default-replies/{cid}')
def delete_default_reply(cid: str, _: None = Depends(require_auth)):
    """删除指定账号的默认回复设置"""
    from db_manager import db_manager
    try:
        success = db_manager.delete_default_reply(cid)
        if success:
            return {'msg': 'default reply deleted'}
        else:
            raise HTTPException(status_code=400, detail='删除失败')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------- 通知渠道管理接口 -------------------------

@app.get('/notification-channels')
def get_notification_channels(_: None = Depends(require_auth)):
    """获取所有通知渠道"""
    from db_manager import db_manager
    try:
        return db_manager.get_notification_channels()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/notification-channels')
def create_notification_channel(channel_data: NotificationChannelIn, _: None = Depends(require_auth)):
    """创建通知渠道"""
    from db_manager import db_manager
    try:
        channel_id = db_manager.create_notification_channel(
            channel_data.name,
            channel_data.type,
            channel_data.config
        )
        return {'msg': 'notification channel created', 'id': channel_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/notification-channels/{channel_id}')
def get_notification_channel(channel_id: int, _: None = Depends(require_auth)):
    """获取指定通知渠道"""
    from db_manager import db_manager
    try:
        channel = db_manager.get_notification_channel(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail='通知渠道不存在')
        return channel
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put('/notification-channels/{channel_id}')
def update_notification_channel(channel_id: int, channel_data: NotificationChannelUpdate, _: None = Depends(require_auth)):
    """更新通知渠道"""
    from db_manager import db_manager
    try:
        success = db_manager.update_notification_channel(
            channel_id,
            channel_data.name,
            channel_data.config,
            channel_data.enabled
        )
        if success:
            return {'msg': 'notification channel updated'}
        else:
            raise HTTPException(status_code=404, detail='通知渠道不存在')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete('/notification-channels/{channel_id}')
def delete_notification_channel(channel_id: int, _: None = Depends(require_auth)):
    """删除通知渠道"""
    from db_manager import db_manager
    try:
        success = db_manager.delete_notification_channel(channel_id)
        if success:
            return {'msg': 'notification channel deleted'}
        else:
            raise HTTPException(status_code=404, detail='通知渠道不存在')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------- 消息通知配置接口 -------------------------

@app.get('/message-notifications')
def get_all_message_notifications(_: None = Depends(require_auth)):
    """获取所有账号的消息通知配置"""
    from db_manager import db_manager
    try:
        return db_manager.get_all_message_notifications()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/message-notifications/{cid}')
def get_account_notifications(cid: str, _: None = Depends(require_auth)):
    """获取指定账号的消息通知配置"""
    from db_manager import db_manager
    try:
        return db_manager.get_account_notifications(cid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/message-notifications/{cid}')
def set_message_notification(cid: str, notification_data: MessageNotificationIn, _: None = Depends(require_auth)):
    """设置账号的消息通知"""
    from db_manager import db_manager
    try:
        # 检查账号是否存在
        all_cookies = db_manager.get_all_cookies()
        if cid not in all_cookies:
            raise HTTPException(status_code=404, detail='账号不存在')

        # 检查通知渠道是否存在
        channel = db_manager.get_notification_channel(notification_data.channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail='通知渠道不存在')

        success = db_manager.set_message_notification(cid, notification_data.channel_id, notification_data.enabled)
        if success:
            return {'msg': 'message notification set'}
        else:
            raise HTTPException(status_code=400, detail='设置失败')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete('/message-notifications/account/{cid}')
def delete_account_notifications(cid: str, _: None = Depends(require_auth)):
    """删除账号的所有消息通知配置"""
    from db_manager import db_manager
    try:
        success = db_manager.delete_account_notifications(cid)
        if success:
            return {'msg': 'account notifications deleted'}
        else:
            raise HTTPException(status_code=404, detail='账号通知配置不存在')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete('/message-notifications/{notification_id}')
def delete_message_notification(notification_id: int, _: None = Depends(require_auth)):
    """删除消息通知配置"""
    from db_manager import db_manager
    try:
        success = db_manager.delete_message_notification(notification_id)
        if success:
            return {'msg': 'message notification deleted'}
        else:
            raise HTTPException(status_code=404, detail='通知配置不存在')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------- 系统设置接口 -------------------------

@app.get('/system-settings')
def get_system_settings(_: None = Depends(require_auth)):
    """获取系统设置（排除敏感信息）"""
    from db_manager import db_manager
    try:
        settings = db_manager.get_all_system_settings()
        # 移除敏感信息
        if 'admin_password_hash' in settings:
            del settings['admin_password_hash']
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put('/system-settings/password')
def update_admin_password(password_data: PasswordUpdateIn, _: None = Depends(require_auth)):
    """更新管理员密码"""
    from db_manager import db_manager
    try:
        # 验证当前密码
        if not db_manager.verify_admin_password(password_data.current_password):
            raise HTTPException(status_code=400, detail='当前密码错误')

        # 更新密码
        success = db_manager.update_admin_password(password_data.new_password)
        if success:
            return {'msg': 'password updated'}
        else:
            raise HTTPException(status_code=400, detail='密码更新失败')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put('/system-settings/{key}')
def update_system_setting(key: str, setting_data: SystemSettingIn, _: None = Depends(require_auth)):
    """更新系统设置"""
    from db_manager import db_manager
    try:
        # 禁止直接修改密码哈希
        if key == 'admin_password_hash':
            raise HTTPException(status_code=400, detail='请使用密码修改接口')

        success = db_manager.set_system_setting(key, setting_data.value, setting_data.description)
        if success:
            return {'msg': 'system setting updated'}
        else:
            raise HTTPException(status_code=400, detail='更新失败')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





@app.delete("/cookies/{cid}")
def remove_cookie(cid: str, _: None = Depends(require_auth)):
    if cookie_manager.manager is None:
        raise HTTPException(status_code=500, detail="CookieManager 未就绪")
    try:
        cookie_manager.manager.remove_cookie(cid)
        return {"msg": "removed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))





class KeywordIn(BaseModel):
    keywords: Dict[str, str]  # key -> reply


@app.get("/keywords/{cid}")
def get_keywords(cid: str, _: None = Depends(require_auth)):
    if cookie_manager.manager is None:
        raise HTTPException(status_code=500, detail="CookieManager 未就绪")
    return cookie_manager.manager.get_keywords(cid)


@app.post("/keywords/{cid}")
def update_keywords(cid: str, body: KeywordIn, _: None = Depends(require_auth)):
    if cookie_manager.manager is None:
        raise HTTPException(status_code=500, detail="CookieManager 未就绪")
    kw_list = [(k, v) for k, v in body.keywords.items()]
    cookie_manager.manager.update_keywords(cid, kw_list)
    return {"msg": "updated", "count": len(kw_list)}


# 卡券管理API
@app.get("/cards")
def get_cards(_: None = Depends(require_auth)):
    """获取卡券列表"""
    try:
        from db_manager import db_manager
        cards = db_manager.get_all_cards()
        return cards
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cards")
def create_card(card_data: dict, _: None = Depends(require_auth)):
    """创建新卡券"""
    try:
        from db_manager import db_manager
        card_id = db_manager.create_card(
            name=card_data.get('name'),
            card_type=card_data.get('type'),
            api_config=card_data.get('api_config'),
            text_content=card_data.get('text_content'),
            data_content=card_data.get('data_content'),
            description=card_data.get('description'),
            enabled=card_data.get('enabled', True)
        )
        return {"id": card_id, "message": "卡券创建成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cards/{card_id}")
def get_card(card_id: int, _: None = Depends(require_auth)):
    """获取单个卡券详情"""
    try:
        from db_manager import db_manager
        card = db_manager.get_card_by_id(card_id)
        if card:
            return card
        else:
            raise HTTPException(status_code=404, detail="卡券不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/cards/{card_id}")
def update_card(card_id: int, card_data: dict, _: None = Depends(require_auth)):
    """更新卡券"""
    try:
        from db_manager import db_manager
        success = db_manager.update_card(
            card_id=card_id,
            name=card_data.get('name'),
            card_type=card_data.get('type'),
            api_config=card_data.get('api_config'),
            text_content=card_data.get('text_content'),
            data_content=card_data.get('data_content'),
            description=card_data.get('description'),
            enabled=card_data.get('enabled', True)
        )
        if success:
            return {"message": "卡券更新成功"}
        else:
            raise HTTPException(status_code=404, detail="卡券不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 自动发货规则API
@app.get("/delivery-rules")
def get_delivery_rules(_: None = Depends(require_auth)):
    """获取发货规则列表"""
    try:
        from db_manager import db_manager
        rules = db_manager.get_all_delivery_rules()
        return rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/delivery-rules")
def create_delivery_rule(rule_data: dict, _: None = Depends(require_auth)):
    """创建新发货规则"""
    try:
        from db_manager import db_manager
        rule_id = db_manager.create_delivery_rule(
            keyword=rule_data.get('keyword'),
            card_id=rule_data.get('card_id'),
            delivery_count=rule_data.get('delivery_count', 1),
            enabled=rule_data.get('enabled', True),
            description=rule_data.get('description')
        )
        return {"id": rule_id, "message": "发货规则创建成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/delivery-rules/{rule_id}")
def get_delivery_rule(rule_id: int, _: None = Depends(require_auth)):
    """获取单个发货规则详情"""
    try:
        from db_manager import db_manager
        rule = db_manager.get_delivery_rule_by_id(rule_id)
        if rule:
            return rule
        else:
            raise HTTPException(status_code=404, detail="发货规则不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/delivery-rules/{rule_id}")
def update_delivery_rule(rule_id: int, rule_data: dict, _: None = Depends(require_auth)):
    """更新发货规则"""
    try:
        from db_manager import db_manager
        success = db_manager.update_delivery_rule(
            rule_id=rule_id,
            keyword=rule_data.get('keyword'),
            card_id=rule_data.get('card_id'),
            delivery_count=rule_data.get('delivery_count', 1),
            enabled=rule_data.get('enabled', True),
            description=rule_data.get('description')
        )
        if success:
            return {"message": "发货规则更新成功"}
        else:
            raise HTTPException(status_code=404, detail="发货规则不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cards/{card_id}")
def delete_card(card_id: int, _: None = Depends(require_auth)):
    """删除卡券"""
    try:
        from db_manager import db_manager
        success = db_manager.delete_card(card_id)
        if success:
            return {"message": "卡券删除成功"}
        else:
            raise HTTPException(status_code=404, detail="卡券不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/delivery-rules/{rule_id}")
def delete_delivery_rule(rule_id: int, _: None = Depends(require_auth)):
    """删除发货规则"""
    try:
        from db_manager import db_manager
        success = db_manager.delete_delivery_rule(rule_id)
        if success:
            return {"message": "发货规则删除成功"}
        else:
            raise HTTPException(status_code=404, detail="发货规则不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 备份和恢复 API ====================

@app.get("/backup/export")
def export_backup(_: None = Depends(require_auth)):
    """导出系统备份"""
    try:
        from db_manager import db_manager
        backup_data = db_manager.export_backup()

        # 生成文件名
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"xianyu_backup_{timestamp}.json"

        # 返回JSON响应，设置下载头
        response = JSONResponse(content=backup_data)
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-Type"] = "application/json"

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出备份失败: {str(e)}")


@app.post("/backup/import")
def import_backup(file: UploadFile = File(...), _: None = Depends(require_auth)):
    """导入系统备份"""
    try:
        # 验证文件类型
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="只支持JSON格式的备份文件")

        # 读取文件内容
        content = file.file.read()
        backup_data = json.loads(content.decode('utf-8'))

        # 导入备份
        from db_manager import db_manager
        success = db_manager.import_backup(backup_data)

        if success:
            return {"message": "备份导入成功"}
        else:
            raise HTTPException(status_code=400, detail="备份导入失败")

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="备份文件格式无效")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入备份失败: {str(e)}")


# ==================== 商品管理 API ====================

@app.get("/items")
def get_all_items(_: None = Depends(require_auth)):
    """获取所有商品信息"""
    try:
        items = db_manager.get_all_items()
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取商品信息失败: {str(e)}")


@app.get("/items/cookie/{cookie_id}")
def get_items_by_cookie(cookie_id: str, _: None = Depends(require_auth)):
    """获取指定Cookie的商品信息"""
    try:
        items = db_manager.get_items_by_cookie(cookie_id)
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取商品信息失败: {str(e)}")


@app.get("/items/{cookie_id}/{item_id}")
def get_item_detail(cookie_id: str, item_id: str, _: None = Depends(require_auth)):
    """获取商品详情"""
    try:
        item = db_manager.get_item_info(cookie_id, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="商品不存在")
        return {"item": item}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取商品详情失败: {str(e)}")


class ItemDetailUpdate(BaseModel):
    item_detail: str


@app.put("/items/{cookie_id}/{item_id}")
def update_item_detail(
    cookie_id: str,
    item_id: str,
    update_data: ItemDetailUpdate,
    _: None = Depends(require_auth)
):
    """更新商品详情"""
    try:
        success = db_manager.update_item_detail(cookie_id, item_id, update_data.item_detail)
        if success:
            return {"message": "商品详情更新成功"}
        else:
            raise HTTPException(status_code=400, detail="更新失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新商品详情失败: {str(e)}")


@app.delete("/items/{cookie_id}/{item_id}")
def delete_item_info(
    cookie_id: str,
    item_id: str,
    _: None = Depends(require_auth)
):
    """删除商品信息"""
    try:
        success = db_manager.delete_item_info(cookie_id, item_id)
        if success:
            return {"message": "商品信息删除成功"}
        else:
            raise HTTPException(status_code=404, detail="商品信息不存在")
    except Exception as e:
        logger.error(f"删除商品信息异常: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


class BatchDeleteRequest(BaseModel):
    items: List[dict]  # [{"cookie_id": "xxx", "item_id": "yyy"}, ...]


class AIReplySettings(BaseModel):
    ai_enabled: bool
    model_name: str = "qwen-plus"
    api_key: str = ""
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    max_discount_percent: int = 10
    max_discount_amount: int = 100
    max_bargain_rounds: int = 3
    custom_prompts: str = ""


@app.delete("/items/batch")
def batch_delete_items(
    request: BatchDeleteRequest,
    _: None = Depends(require_auth)
):
    """批量删除商品信息"""
    try:
        if not request.items:
            raise HTTPException(status_code=400, detail="删除列表不能为空")

        success_count = db_manager.batch_delete_item_info(request.items)
        total_count = len(request.items)

        return {
            "message": f"批量删除完成",
            "success_count": success_count,
            "total_count": total_count,
            "failed_count": total_count - success_count
        }
    except Exception as e:
        logger.error(f"批量删除商品信息异常: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


# ==================== AI回复管理API ====================

@app.get("/ai-reply-settings/{cookie_id}")
def get_ai_reply_settings(cookie_id: str, _: None = Depends(require_auth)):
    """获取指定账号的AI回复设置"""
    try:
        settings = db_manager.get_ai_reply_settings(cookie_id)
        return settings
    except Exception as e:
        logger.error(f"获取AI回复设置异常: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@app.put("/ai-reply-settings/{cookie_id}")
def update_ai_reply_settings(cookie_id: str, settings: AIReplySettings, _: None = Depends(require_auth)):
    """更新指定账号的AI回复设置"""
    try:
        # 检查账号是否存在
        if cookie_manager.manager is None:
            raise HTTPException(status_code=500, detail='CookieManager 未就绪')

        if cookie_id not in cookie_manager.manager.cookies:
            raise HTTPException(status_code=404, detail='账号不存在')

        # 保存设置
        settings_dict = settings.dict()
        success = db_manager.save_ai_reply_settings(cookie_id, settings_dict)

        if success:
            # 清理客户端缓存，强制重新创建
            ai_reply_engine.clear_client_cache(cookie_id)

            # 如果启用了AI回复，记录日志
            if settings.ai_enabled:
                logger.info(f"账号 {cookie_id} 启用AI回复")
            else:
                logger.info(f"账号 {cookie_id} 禁用AI回复")

            return {"message": "AI回复设置更新成功"}
        else:
            raise HTTPException(status_code=400, detail="更新失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新AI回复设置异常: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@app.get("/ai-reply-settings")
def get_all_ai_reply_settings(_: None = Depends(require_auth)):
    """获取所有账号的AI回复设置"""
    try:
        settings = db_manager.get_all_ai_reply_settings()
        return settings
    except Exception as e:
        logger.error(f"获取所有AI回复设置异常: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@app.post("/ai-reply-test/{cookie_id}")
def test_ai_reply(cookie_id: str, test_data: dict, _: None = Depends(require_auth)):
    """测试AI回复功能"""
    try:
        # 检查账号是否存在
        if cookie_manager.manager is None:
            raise HTTPException(status_code=500, detail='CookieManager 未就绪')

        if cookie_id not in cookie_manager.manager.cookies:
            raise HTTPException(status_code=404, detail='账号不存在')

        # 检查是否启用AI回复
        if not ai_reply_engine.is_ai_enabled(cookie_id):
            raise HTTPException(status_code=400, detail='该账号未启用AI回复')

        # 构造测试数据
        test_message = test_data.get('message', '你好')
        test_item_info = {
            'title': test_data.get('item_title', '测试商品'),
            'price': test_data.get('item_price', 100),
            'desc': test_data.get('item_desc', '这是一个测试商品')
        }

        # 生成测试回复
        reply = ai_reply_engine.generate_reply(
            message=test_message,
            item_info=test_item_info,
            chat_id=f"test_{int(time.time())}",
            cookie_id=cookie_id,
            user_id="test_user",
            item_id="test_item"
        )

        if reply:
            return {"message": "测试成功", "reply": reply}
        else:
            raise HTTPException(status_code=400, detail="AI回复生成失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试AI回复异常: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


# ==================== 日志管理API ====================

@app.get("/logs")
async def get_logs(lines: int = 200, level: str = None, source: str = None, _: None = Depends(require_auth)):
    """获取实时系统日志"""
    try:
        # 获取文件日志收集器
        collector = get_file_log_collector()

        # 获取日志
        logs = collector.get_logs(lines=lines, level_filter=level, source_filter=source)

        return {"success": True, "logs": logs}

    except Exception as e:
        return {"success": False, "message": f"获取日志失败: {str(e)}", "logs": []}


@app.get("/logs/stats")
async def get_log_stats(_: None = Depends(require_auth)):
    """获取日志统计信息"""
    try:
        collector = get_file_log_collector()
        stats = collector.get_stats()

        return {"success": True, "stats": stats}

    except Exception as e:
        return {"success": False, "message": f"获取日志统计失败: {str(e)}", "stats": {}}


@app.post("/logs/clear")
async def clear_logs(_: None = Depends(require_auth)):
    """清空日志"""
    try:
        collector = get_file_log_collector()
        collector.clear_logs()

        return {"success": True, "message": "日志已清空"}

    except Exception as e:
        return {"success": False, "message": f"清空日志失败: {str(e)}"}


# ==================== 商品管理API ====================

@app.post("/items/get-all-from-account")
async def get_all_items_from_account(request: dict, _: None = Depends(require_auth)):
    """从指定账号获取所有商品信息"""
    try:
        cookie_id = request.get('cookie_id')
        if not cookie_id:
            return {"success": False, "message": "缺少cookie_id参数"}

        # 获取指定账号的cookie信息
        cookie_info = db_manager.get_cookie_by_id(cookie_id)
        if not cookie_info:
            return {"success": False, "message": "未找到指定的账号信息"}

        cookies_str = cookie_info.get('cookies_str', '')
        if not cookies_str:
            return {"success": False, "message": "账号cookie信息为空"}

        # 创建XianyuLive实例，传入正确的cookie_id
        from XianyuAutoAsync import XianyuLive
        xianyu_instance = XianyuLive(cookies_str, cookie_id)

        # 调用获取商品信息的方法
        logger.info(f"开始获取账号 {cookie_id} 的所有商品信息")
        result = await xianyu_instance.get_item_list_info()

        # 关闭session
        await xianyu_instance.close_session()

        if result.get('error'):
            logger.error(f"获取商品信息失败: {result['error']}")
            return {"success": False, "message": result['error']}
        else:
            logger.info(f"成功获取账号 {cookie_id} 的 {result.get('total_count', 0)} 个商品")
            return {
                "success": True,
                "message": f"成功获取 {result.get('total_count', 0)} 个商品，详细信息已打印到控制台",
                "total_count": result.get('total_count', 0)
            }

    except Exception as e:
        logger.error(f"获取账号商品信息异常: {str(e)}")
        return {"success": False, "message": f"获取商品信息异常: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)