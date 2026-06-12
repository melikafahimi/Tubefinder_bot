import os
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی از فایل .env (اختیاری)
load_dotenv()

# کلیدهای API
TELEGRAM_TOKEN = "8771586006:AAFbrerbnmbbhBxG3mNzqijcO8w7bFjjhG8"
YOUTUBE_API_KEY = "AIzaSyClIbELQjQjnE3VQg19_yOIo7PKT0I5CvA"
OPENAI_API_KEY = "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"

# اگر از فایل .env استفاده می‌کنید، می‌توانید به این صورت مقادیر را بخوانید:
# TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
