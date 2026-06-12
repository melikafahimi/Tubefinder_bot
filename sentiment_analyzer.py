from googleapiclient.discovery import build
from textblob import TextBlob
from config import YOUTUBE_API_KEY

def get_video_comments(video_id, max_comments=100):
    """
    دریافت کامنت‌های یک ویدیوی YouTube
    
    Args:
        video_id (str): آیدی ویدیوی YouTube
        max_comments (int): حداکثر تعداد کامنت برای دریافت
    
    Returns:
        list: لیستی از کامنت‌ها با اطلاعات مربوطه
    """
    try:
        # ساخت سرویس YouTube
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        
        comments = []
        next_page_token = None
        
        while len(comments) < max_comments:
            # دریافت کامنت‌ها
            request = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=min(100, max_comments - len(comments)),
                pageToken=next_page_token,
                textFormat='plainText'
            )
            
            response = request.execute()
            
            # استخراج کامنت‌ها
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'author': comment['authorDisplayName'],
                    'text': comment['textDisplay'],
                    'likes': comment['likeCount'],
                    'published_at': comment['publishedAt']
                })
            
            # بررسی وجود صفحه بعدی
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        return comments[:max_comments]
    
    except Exception as e:
        print(f"خطا در دریافت کامنت‌ها: {e}")
        return []

# مثال استفاده
if __name__ == "__main__":
    video_id = "YOUR_VIDEO_ID"  # آیدی ویدیو را وارد کنید
    comments = get_video_comments(video_id, 50)
    
    for i, comment in enumerate(comments, 1):
        print(f"{i}. {comment['author']}: {comment['text'][:100]}...")
