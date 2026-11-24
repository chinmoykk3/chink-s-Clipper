import os
import re
from typing import Dict, List, Any, Optional
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        r'(?:shorts\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_info(url: str) -> Dict[str, Any]:
    """Extract metadata for a YouTube video without downloading."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            'id': info.get('id'),
            'title': info.get('title'),
            'duration': info.get('duration'),
            'uploader': info.get('uploader'),
            'thumbnail': info.get('thumbnail'),
            'description': info.get('description', '')[:500]
        }

def get_transcript(video_id: str) -> List[Dict[str, Any]]:
    """
    Fetch transcript using youtube-transcript-api.
    Returns list of dicts: [{'text': str, 'start': float, 'duration': float}]
    """
    try:
        # Try fetching official or generated transcripts
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
        return transcript_list
    except Exception as e:
        print(f"Direct transcript error: {e}")
        # Try any available language
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            # Find first available transcript
            for t in transcript_list:
                return t.fetch()
        except Exception as e2:
            print(f"Fallback transcript error: {e2}")
            return []

def download_video(url: str, output_path: str, ffmpeg_path: Optional[str] = None) -> str:
    """Download best 1080p video with audio merged."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    ydl_opts = {
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'quiet': False,
        'no_warnings': True,
    }
    if ffmpeg_path:
        ydl_opts['ffmpeg_location'] = ffmpeg_path
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        
    return output_path
