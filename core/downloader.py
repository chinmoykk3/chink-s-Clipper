import os
import re
import json
import urllib.request
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
    Fetch transcript using youtube-transcript-api (supporting both new and legacy API),
    with automatic fallback to yt-dlp extracted captions.
    Returns list of dicts: [{'text': str, 'start': float, 'duration': float}]
    """
    results: List[Dict[str, Any]] = []

    # 1. Primary: youtube-transcript-api
    try:
        api = YouTubeTranscriptApi()
        snippets = None
        
        # New API (v1.2.0+)
        if hasattr(api, 'fetch'):
            try:
                snippets = api.fetch(video_id, languages=('en', 'en-US', 'en-GB'))
            except Exception:
                try:
                    t_list = api.list(video_id)
                    for t in t_list:
                        snippets = t.fetch()
                        break
                except Exception:
                    snippets = None
        # Legacy static method fallback
        elif hasattr(YouTubeTranscriptApi, 'get_transcript'):
            try:
                snippets = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
            except Exception:
                snippets = None

        if snippets:
            for s in snippets:
                txt = getattr(s, 'text', '') if not isinstance(s, dict) else s.get('text', '')
                txt = txt.replace('\u200b', '').replace('\n', ' ').strip()
                start = getattr(s, 'start', 0.0) if not isinstance(s, dict) else s.get('start', 0.0)
                dur = getattr(s, 'duration', 0.0) if not isinstance(s, dict) else s.get('duration', 0.0)
                if txt:
                    results.append({'text': txt, 'start': float(start), 'duration': float(dur)})
            if results:
                return results
    except Exception as e:
        print(f"youtube-transcript-api error: {e}")

    # 2. Secondary Fallback: yt-dlp subtitle JSON extraction
    try:
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'quiet': True,
            'no_warnings': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            subs = info.get('subtitles', {}) or info.get('automatic_captions', {})
            en_subs = subs.get('en') or subs.get('en-US') or subs.get('en-orig')
            
            if en_subs:
                # Find json3 format
                json_sub = next((s for s in en_subs if s.get('ext') == 'json3'), None)
                if not json_sub:
                    json_sub = en_subs[0]
                
                req = urllib.request.Request(json_sub['url'], headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as resp:
                    sub_data = json.loads(resp.read().decode('utf-8'))
                    events = sub_data.get('events', [])
                    for ev in events:
                        segs = ev.get('segs', [])
                        text = "".join(seg.get('utf8', '') for seg in segs).strip()
                        text = text.replace('\u200b', '').replace('\n', ' ').strip()
                        start = ev.get('tStartMs', 0) / 1000.0
                        dur = ev.get('dDurationMs', 0) / 1000.0
                        if text:
                            results.append({'text': text, 'start': float(start), 'duration': float(dur)})
    except Exception as e2:
        print(f"yt-dlp subtitle extraction error: {e2}")

    return results

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
