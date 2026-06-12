from googleapiclient.discovery import build
from config import YOUTUBE_API_KEY

def search_videos_by_topic(topic, max_results=10):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    search_response = youtube.search().list(
        q=topic,
        part='id,snippet',
        type='video',
        maxResults=max_results,
        order='relevance'
    ).execute()
    
    videos = []
    for search_result in search_response.get('items', []):
        video_id = search_result['id']['videoId']
        video_info = {
            'video_id': video_id,
            'title': search_result['snippet']['title'],
            'description': search_result['snippet']['description'],
            'published_at': search_result['snippet']['publishedAt'],
            'thumbnail': search_result['snippet']['thumbnails']['high']['url'],
            'video_url': f"https://www.youtube.com/watch?v={video_id}"
        }
        videos.append(video_info)
    
    return videos

def get_video_statistics(video_id):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    stats_response = youtube.videos().list(
        part='statistics',
        id=video_id
    ).execute()
    
    if not stats_response.get('items'):
        return None
    
    stats = stats_response['items'][0]['statistics']
    return {
        'like_count': int(stats.get('likeCount', 0)),
        'comment_count': int(stats.get('commentCount', 0)),
        'view_count': int(stats.get('viewCount', 0))
    }
