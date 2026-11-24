import os
from typing import List, Dict, Any

def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS subtitle timestamp format: H:MM:SS.cs"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int(round((seconds - int(seconds)) * 100))
    if centisecs >= 100:
        centisecs = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{centisecs:02d}"

def generate_ass_subtitles(
    transcript_items: List[Dict[str, Any]],
    clip_start: float,
    clip_end: float,
    output_ass_path: str,
    power_words: List[str] = None,
    font_name: str = "Arial",
    font_size: int = 16,
    primary_color: str = "&H00FFFFFF",      # White (AABBGGRR)
    highlight_color: str = "&H0000FFFF",    # Bright Yellow (AABBGGRR)
    outline_color: str = "&H00000000",      # Black outline
    words_per_group: int = 4
) -> str:
    """
    Generate Advanced Substation Alpha (.ass) subtitles with bold kinetic styling.
    - Groups words into snappy 3-4 word phrases for high visual retention.
    - Colorizes power words to pop out.
    """
    if power_words is None:
        power_words = []
    power_words_upper = [w.strip().upper() for w in power_words if w.strip()]

    # ASS Header with Styles
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},68,{primary_color},&H000000FF,{outline_color},&H80000000,-1,0,0,0,100,100,2,0,1,5,3,2,60,60,420,1
Style: HookHeader,{font_name},64,&H0000FFFF,&H000000FF,{outline_color},&HB0000000,-1,0,0,0,100,100,2,0,1,6,4,8,60,60,250,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    # Filter transcript items that fall inside the clip boundaries
    relevant_items = []
    for item in transcript_items:
        start = item.get('start', 0.0)
        duration = item.get('duration', 0.0)
        end = start + duration
        
        # Overlaps with clip
        if end >= clip_start and start <= clip_end:
            # Shift relative to clip start
            rel_start = max(0.0, start - clip_start)
            rel_end = min(clip_end - clip_start, end - clip_start)
            text = item.get('text', '').strip()
            if text and rel_end > rel_start:
                relevant_items.append({
                    'rel_start': rel_start,
                    'rel_end': rel_end,
                    'text': text
                })

    # Group into punchy chunks
    for i in range(0, len(relevant_items), words_per_group):
        chunk = relevant_items[i:i + words_per_group]
        chunk_start = chunk[0]['rel_start']
        chunk_end = chunk[-1]['rel_end']
        
        words = []
        for c in chunk:
            clean_word = c['text'].strip()
            # If word is in power words, highlight it
            clean_word_no_punct = "".join(ch for ch in clean_word if ch.isalnum()).upper()
            if clean_word_no_punct in power_words_upper:
                words.append(f"{{\\c{highlight_color}\\b1}}{clean_word}{{\\r}}")
            else:
                words.append(clean_word)
                
        chunk_text = " ".join(words).upper()
        start_str = format_ass_time(chunk_start)
        end_str = format_ass_time(chunk_end)
        
        ass_content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{chunk_text}\n"

    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    return output_ass_path
