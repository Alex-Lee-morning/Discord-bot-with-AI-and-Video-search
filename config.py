import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Discord 配置
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    CHANNEL_ID = int(os.getenv("CHANNEL_ID", "Fill with your default channel ID"))
    
    # DeepSeek 配置
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "")
    
    # 权限配置
    ALLOWED_USERS = [int(x) for x in os.getenv("ALLOWED_USERS", "Your ID").split(",")]
    
    # 功能配置
    MAX_VIDEO_SIZE_MB = 10
    MAX_HISTORY_LENGTH = 20
    SEARCH_RESULTS_PER_PAGE = 5
    VIDEO_QUALITY = "bestvideo[height<=360]+bestaudio/best"
    ACTIVITY_TIMEOUT = 3600  # 1小时
    
    # 文件路径
    TEMP_DIR = "temp"
    LOG_FILE = "bot.log"

# 创建临时目录
if not os.path.exists(Config.TEMP_DIR):
    os.makedirs(Config.TEMP_DIR)