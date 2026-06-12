import telebot
import requests
import os
import re
from textblob import TextBlob
from config import TELEGRAM_TOKEN, YOUTUBE_API_KEY

# غیرفعال کردن پروکسی
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# کلمات خوب برای آموزش واقعی
GOOD_KEYWORDS = [
    'آموزش کامل', 'از صفر تا صد', 'مقدماتی تا پیشرفته', 'پروژه محور',
    'گام به گام', 'صفر تا صد', 'آموزش جامع', 'یادگیری', 'آموزش عملی',
    'tutorial', 'complete course', 'step by step', 'full course',
    'آموزش صفر تا صد', 'همه چیز درباره', 'masterclass', 'course',
    'آموزش', 'learn', 'راهنما', 'guide'
]

# کلمات بد
BAD_KEYWORDS = [
    'کوتاه', 'تیزر', 'کلیپ', 'موزیک', 'میم', 'سرگرمی', 'طنز',
    'تریلر', 'پیش نمایش', 'اهنگ', 'موزیک ویدیو', 'لایو', 'استریم',
    'گیم پلی', 'خنده دار', 'short', 'clip', 'teaser', 'trailer', 'funny',
    'shorts', '#shorts', 'ترند', 'کمدی'
]

def clean_text(text):
    """پاکسازی متن از کاراکترهای مشکل‌دار"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, '\\' + char)
    return text

def is_real_educational_video(title, description, duration_seconds):
    """بررسی می‌کند که آیا ویدیو یک آموزش واقعی است"""
    title_lower = title.lower()
    desc_lower = description.lower() if description else ""
    
    if duration_seconds < 480:
        return False
    
    for bad in BAD_KEYWORDS:
        if bad in title_lower:
            return False
    
    has_good_keyword = False
    for good in GOOD_KEYWORDS:
        if good in title_lower or good in desc_lower:
            has_good_keyword = True
            break
    
    if not has_good_keyword:
        return False
    
    if len(description) < 80:
        return False
    
    return True

def search_videos_by_topic(topic, max_results=25):
    """جستجوی ویدیوها"""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': topic,
        'type': 'video',
        'maxResults': max_results,
        'key': YOUTUBE_API_KEY,
        'videoDuration': 'long'
    }
    
    try:
        response = requests.get(url, params=params, proxies={"http": None, "https": None})
        data = response.json()
        
        videos = []
        if 'items' in data:
            for item in data['items']:
                video_info = {
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'][:500] if item['snippet']['description'] else "",
                    'video_url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'channel_id': item['snippet']['channelId'],
                    'channel_title': item['snippet']['channelTitle']
                }
                videos.append(video_info)
        return videos
    except Exception as e:
        print(f"خطا در جستجو: {e}")
        return []

def get_video_details(video_id):
    """دریافت جزئیات ویدیو"""
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        'part': 'statistics,contentDetails',
        'id': video_id,
        'key': YOUTUBE_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, proxies={"http": None, "https": None})
        data = response.json()
        
        if 'items' in data and data['items']:
            item = data['items'][0]
            duration_str = item['contentDetails']['duration']
            duration_seconds = 0
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                duration_seconds = hours * 3600 + minutes * 60 + seconds
            
            stats = item['statistics']
            return {
                'duration_seconds': duration_seconds,
                'duration_minutes': round(duration_seconds / 60),
                'like_count': int(stats.get('likeCount', 0)),
                'view_count': int(stats.get('viewCount', 0)),
                'comment_count': int(stats.get('commentCount', 0))
            }
        return None
    except Exception as e:
        print(f"خطا: {e}")
        return None

def get_channel_stats(channel_id):
    """دریافت آمار کانال"""
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        'part': 'statistics',
        'id': channel_id,
        'key': YOUTUBE_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, proxies={"http": None, "https": None})
        data = response.json()
        
        if 'items' in data and data['items']:
            stats = data['items'][0]['statistics']
            return {
                'subscriber_count': int(stats.get('subscriberCount', 0))
            }
        return None
    except Exception as e:
        return None

def get_video_comments(video_id, max_comments=30):
    """دریافت کامنت‌ها"""
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        'part': 'snippet',
        'videoId': video_id,
        'maxResults': min(max_comments, 100),
        'key': YOUTUBE_API_KEY
    }
    
    comments = []
    try:
        response = requests.get(url, params=params, proxies={"http": None, "https": None})
        data = response.json()
        
        if 'items' in data:
            for item in data['items']:
                comment_text = item['snippet']['topLevelComment']['snippet']['textDisplay']
                like_count = item['snippet']['topLevelComment']['snippet']['likeCount']
                comments.append({'text': comment_text, 'like_count': like_count})
    except Exception as e:
        pass
    
    return comments

def analyze_sentiment(comment_text):
    """تحلیل احساسات"""
    analysis = TextBlob(comment_text)
    polarity = analysis.sentiment.polarity
    if polarity > 0.1:
        return 'positive'
    elif polarity < -0.1:
        return 'negative'
    return 'neutral'

def calculate_comment_quality_score(comments):
    """محاسبه کیفیت کامنت‌ها"""
    if not comments:
        return 0.5, 0, 0
    
    positive_count = 0
    thanks_count = 0
    total_score = 0
    
    for comment in comments:
        sentiment = analyze_sentiment(comment['text'])
        if sentiment == 'positive':
            positive_count += 1
            total_score += 0.3
        
        thanks_words = ['ممنون', 'تشکر', 'عالی', 'دمت گرم', 'خوب بود', 'باحال', 'خیلی خوب']
        for word in thanks_words:
            if word in comment['text'].lower():
                thanks_count += 1
                total_score += 0.2
                break
        
        if len(comment['text']) > 100:
            total_score += 0.1
        
        total_score += min(comment['like_count'] / 50, 0.1)
    
    normalized_score = min(total_score / len(comments), 1.0)
    positive_ratio = positive_count / len(comments) if comments else 0
    
    return normalized_score, positive_ratio, thanks_count

def get_quality_emoji(score):
    if score >= 0.85:
        return "🏆 عالی"
    elif score >= 0.7:
        return "⭐ خیلی خوب"
    elif score >= 0.55:
        return "✅ خوب"
    elif score >= 0.4:
        return "👍 متوسط"
    else:
        return "⚠️ ضعیف"

def format_number(num):
    """فرمت کردن اعداد (مثلاً 1000 -> 1K)"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)

@bot.message_handler(commands=['start'])
def start(message):
    welcome = """🎓 ربات جستجوی آموزش‌های یوتیوب

این ربات بهترین آموزش‌ها رو پیدا می‌کنه.

📝 فقط موضوع مورد نظرت رو بفرست!
مثال: آموزش پایتون"""
    bot.reply_to(message, welcome)

@bot.message_handler(func=lambda message: True)
def handle_topic(message):
    topic = message.text.strip()
    user_id = message.chat.id
    
    msg = bot.reply_to(message, f"🔍 در حال جستجوی {topic} ...")
    
    try:
        videos = search_videos_by_topic(topic, max_results=25)
        
        if not videos:
            bot.edit_message_text("❌ ویدیویی پیدا نشد.", user_id, msg.message_id)
            return
        
        bot.edit_message_text(f"✅ {len(videos)} ویدیو پیدا شد. در حال تحلیل...", user_id, msg.message_id)
        
        good_videos = []
        
        for i, video in enumerate(videos):
            bot.edit_message_text(f"📊 بررسی ویدیو {i+1} از {len(videos)}", user_id, msg.message_id)
            
            details = get_video_details(video['video_id'])
            if not details:
                continue
            
            is_educational = is_real_educational_video(
                video['title'], 
                video['description'], 
                details['duration_seconds']
            )
            
            if not is_educational:
                continue
            
            channel_stats = get_channel_stats(video['channel_id'])
            comments = get_video_comments(video['video_id'], max_comments=30)
            
            # محاسبه امتیاز مدت زمان
            duration_score = min(details['duration_minutes'] / 90, 1.0)
            
            # امتیاز لایک
            view_like_ratio = details['like_count'] / max(details['view_count'], 1) * 100
            like_score = min(view_like_ratio / 10, 1.0)
            
            # امتیاز کامنت
            comment_quality, positive_ratio, thanks_count = calculate_comment_quality_score(comments)
            
            # امتیاز کانال
            if channel_stats:
                channel_score = min(channel_stats['subscriber_count'] / 200000, 1.0)
                channel_cred = "معتبر" if channel_stats['subscriber_count'] > 50000 else "معمولی" if channel_stats['subscriber_count'] > 10000 else "جدید"
            else:
                channel_score = 0.3
                channel_cred = "ناشناس"
            
            # امتیاز نهایی
            final_score = (duration_score * 0.35) + (like_score * 0.25) + (comment_quality * 0.20) + (channel_score * 0.10) + (0.1)
            
            if final_score >= 0.3:
                good_videos.append({
                    'video': video,
                    'details': details,
                    'final_score': final_score,
                    'like_score': like_score,
                    'comment_quality': comment_quality,
                    'positive_ratio': positive_ratio,
                    'thanks_count': thanks_count,
                    'channel_cred': channel_cred,
                    'view_like_ratio': round(view_like_ratio, 1)
                })
        
        # ========== تغییر مهم: مرتب‌سازی بر اساس بیشترین تعداد کامنت ==========
        # ویدیوها بر اساس تعداد کامنت (comment_count) از بیشتر به کمتر مرتب می‌شوند
        good_videos.sort(key=lambda x: x['details']['comment_count'], reverse=True)
        
        if not good_videos:
            bot.edit_message_text("❌ ویدیوی مناسبی پیدا نشد.", user_id, msg.message_id)
            return
        
        # ارسال نتایج
        bot.edit_message_text(f"🎯 نتایج جستجو برای: {topic}\n\n📊 مرتب‌سازی بر اساس بیشترین کامنت\n{len(good_videos)} ویدیوی باکیفیت پیدا شد:", user_id, msg.message_id)
        
        for i, v in enumerate(good_videos[:12]):  # حداکثر 12 ویدیو
            quality_emoji = get_quality_emoji(v['final_score'])
            
            # مدت زمان
            duration = v['details']['duration_minutes']
            if duration >= 120:
                duration_emoji = "🔥 فوق‌العاده"
            elif duration >= 60:
                duration_emoji = "📚 دوره جامع"
            elif duration >= 30:
                duration_emoji = "📖 آموزش کامل"
            elif duration >= 15:
                duration_emoji = "📝 آموزش متوسط"
            else:
                duration_emoji = "🎬 کوتاه"
            
            # لینک ویدیو
            video_link = v['video']['video_url']
            
            video_msg = f"""
{i+1}. {v['video']['title'][:65]}

📺 {v['video']['channel_title']}
⭐ {quality_emoji} ({v['final_score']:.0%})
⏱️ {duration} دقیقه ({duration_emoji})
👍 {format_number(v['details']['like_count'])} | 👁️ {format_number(v['details']['view_count'])}
💬 **{format_number(v['details']['comment_count'])} نظر** (بیشترین)
📈 نسبت لایک: {v['view_like_ratio']}%
💬 کامنت مثبت: {v['positive_ratio']:.0%}
👑 کانال: {v['channel_cred']}

🔗 {video_link}
"""
            bot.send_message(user_id, video_msg, disable_web_page_preview=True)
        
        # پیام پایانی
        bot.send_message(user_id, "💡 ویدیوهایی با بیشترین کامنت معمولاً محبوبیت و تعامل بیشتری دارند.")
        
    except Exception as e:
        error_msg = f"❌ خطا: {str(e)[:100]}"
        bot.edit_message_text(error_msg, user_id, msg.message_id)
        print(f"خطا: {e}")

print("✅ ربات در حال اجراست...")
print("📊 ترتیب نتایج بر اساس بیشترین تعداد کامنت")
bot.infinity_polling(timeout=15)
