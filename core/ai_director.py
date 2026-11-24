import os
import json
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

DIRECTOR_SYSTEM_PROMPT = """You are an elite short-form video director and viral growth strategist for platforms like YouTube Shorts, TikTok, and Instagram Reels (producing content on the level of MrBeast, Colin & Samir, and Joe Rogan editors).

Your mission is to analyze a timestamped transcript of a long video and extract the MOST VIRAL, HIGH-RETENTION 30-75 second clips.

CRITICAL RULES FOR SELECTING CLIPS:
1. THE 3-SECOND HOOK: The clip MUST start immediately on a captivating thought, counter-intuitive insight, high-stakes question, or shocking statement. Reject clips that begin with conversational throat-clearing ("Yeah, you know...", "So basically...", "Um...").
2. STANDALONE NARRATIVE ARC: The clip must make 100% sense to someone who has never seen the full video. Structure: [Hook] -> [Context/Tension] -> [Punchline/Resolution]. Never cut mid-sentence or mid-thought.
3. THE PUNCHLINE/RESOLUTION: The ending must stick the landing—either a memorable takeaway, a punchline, or a profound realization.
4. HOOK OVERLAY HEADLINE: Provide a punchy 3-5 word headline in ALL CAPS to display as a top banner overlay for the first 3 seconds to stop the scroll.
5. POWER WORDS: Identify 5-8 crucial power words throughout the transcript to highlight in vibrant colors for retention.

OUTPUT FORMAT:
Return ONLY a valid JSON list of clip objects with NO markdown code fences or conversational text.
Each clip object must follow this exact structure:
[
  {
    "title": "Short descriptive title of the clip",
    "hook_headline": "PUNCHY 3-5 WORD SCROLL STOPPER",
    "start_time": 124.5,
    "end_time": 178.0,
    "duration_seconds": 53.5,
    "hook_quote": "Exact first sentence that hooks the viewer",
    "punchline_quote": "Exact last sentence that sticks the landing",
    "virality_score": 94,
    "reasoning": "Why this will perform well on Shorts/Reels/TikTok",
    "power_words": ["DISASTER", "SECRET", "MILLION", "STOP"]
  }
]
"""

def format_transcript_for_llm(transcript_items: List[Dict[str, Any]], max_chars: int = 100000) -> str:
    """Formats transcript into timestamped text chunks for LLM ingestion."""
    lines = []
    for item in transcript_items:
        start = item.get('start', 0.0)
        minutes = int(start // 60)
        seconds = int(start % 60)
        text = item.get('text', '').strip()
        lines.append(f"[{minutes:02d}:{seconds:02d} | {start:.1f}s] {text}")
        
    full_text = "\n".join(lines)
    if len(full_text) > max_chars:
        return full_text[:max_chars] + "\n...[Transcript truncated due to length]..."
    return full_text

def call_gemini_api(client: genai.Client, prompt: str, api_key: str) -> str:
    """
    Executes prompt using modern Interactions API (gemini-3.8-flash) as recommended by Google AI Studio,
    with automatic fallbacks to generateContent with v1beta.
    """
    # 1. Primary: Interactions API with gemini-3.8-flash
    for m in ['gemini-3.8-flash', 'gemini-2.5-flash', 'gemini-2.0-flash']:
        try:
            interaction = client.interactions.create(
                model=m,
                input=prompt,
                system_instruction=DIRECTOR_SYSTEM_PROMPT,
                response_mime_type="application/json"
            )
            if interaction and getattr(interaction, 'output_text', None):
                return interaction.output_text
        except Exception as e:
            print(f"Interactions API ({m}) error: {e}")

    # 2. Fallback: Models generateContent using v1beta
    beta_client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
    for m in ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-2.5-flash']:
        try:
            res = beta_client.models.generate_content(
                model=m,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=DIRECTOR_SYSTEM_PROMPT,
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )
            if res and res.text:
                return res.text
        except Exception as e2:
            print(f"v1beta generateContent ({m}) error: {e2}")

    raise RuntimeError("Failed to generate clips with Gemini. Please check your API key permissions.")

def analyze_and_extract_clips(
    transcript_items: List[Dict[str, Any]],
    video_title: str = "",
    num_clips: int = 3,
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Analyzes transcript and extracts viral clips using Gemini.
    """
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY is not set. Please provide your free Gemini API key.")
        
    client = genai.Client(api_key=key)
    formatted_transcript = format_transcript_for_llm(transcript_items)
    
    prompt = f"""VIDEO TITLE: "{video_title}"

Here is the full timestamped transcript of the video:
---
{formatted_transcript}
---

Find the top {num_clips} most viral, high-retention clips (30 to 75 seconds each).
Ensure exact timestamp boundaries, punchy hook headlines, and standalone narrative quality.
Return ONLY the JSON list.
"""

    raw_text = call_gemini_api(client, prompt, key).strip()
    
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    raw_text = raw_text.strip()
    
    try:
        clips = json.loads(raw_text)
        return clips
    except Exception as e:
        print(f"Error parsing Gemini response: {e}\nRaw output:\n{raw_text}")
        return []
