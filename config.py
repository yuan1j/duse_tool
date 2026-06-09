import os

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, os.environ.get("DB_FILE", "data_entry_system.db"))
LOG_FILE = os.path.join(BASE_DIR, os.environ.get("LOG_FILE", "app.log"))

FIELD_TYPES = ["text", "number", "date", "textarea", "select", "email", "tel"]
FIELD_TYPES_CN = {
    "text": "单行文本",
    "number": "数字",
    "date": "日期",
    "textarea": "多行文本",
    "select": "下拉选择",
    "email": "邮箱",
    "tel": "电话"
}

DEFAULT_AI_TIPS = {
    "text": "简短描述，不超过50字",
    "number": "请输入数字",
    "date": "格式：YYYY-MM-DD",
    "textarea": "详细描述，可换行",
    "select": "从下拉列表中选择",
    "email": "格式：example@domain.com",
    "tel": "格式：13800138000"
}

APP_TITLE = os.environ.get("APP_TITLE", "通用数据填报系统")
APP_VERSION = os.environ.get("APP_VERSION", "2.0.0")
APP_PORT = int(os.environ.get("APP_PORT", "7860"))
APP_SHARE = os.environ.get("APP_SHARE", "false").lower() == "true"

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
DASHSCOPE_MODEL = os.environ.get("DASHSCOPE_MODEL", "qwen-plus")
DASHSCOPE_FAST_MODEL = os.environ.get("DASHSCOPE_FAST_MODEL", "qwen-turbo")
DASHSCOPE_TIMEOUT = int(os.environ.get("DASHSCOPE_TIMEOUT", "15"))
DASHSCOPE_TEMPERATURE = float(os.environ.get("DASHSCOPE_TEMPERATURE", "0.7"))
DASHSCOPE_TOP_P = float(os.environ.get("DASHSCOPE_TOP_P", "0.9"))
ENABLE_DASHSCOPE = DASHSCOPE_API_KEY != ""

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
