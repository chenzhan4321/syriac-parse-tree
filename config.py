import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 获取 API key
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')

# 验证 API key 是否存在
if not DASHSCOPE_API_KEY:
    raise ValueError("DASHSCOPE_API_KEY not found in environment variables") 