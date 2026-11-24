import os
import streamlit as st
from dotenv import load_dotenv

from core.downloader import get_video_info, extract_video_id, get_transcript, download_video
from core.ai_director import analyze_and_extract_clips
from core.subtitle_engine import generate_ass_subtitles
from core.video_processor import render_short_clip, get_ffmpeg_binary

# Load local environment variables if .env exists
load_dotenv()

st.set_page_config(
    page_title="AI Clipper Studio",
    page_icon="🎬",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF8533);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .score-badge {
        background-color: #10B981;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    .hook-banner {
        background-color: #1E293B;
        border-left: 4px solid #F59E0B;
        padding: 12px;
        border-radius: 4px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🎬 AI Clipper Studio</h1>', unsafe_allow_html=True)
st.caption("Transform long YouTube videos into viral, high-retention 9:16 Shorts & Reels — 100% Free")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    env_key = os.getenv("GEMINI_API_KEY", "")
    api_key = st.text_input(
        "Google Gemini API Key",
        value=env_key,
        type="password",
        help="Get a 100% free Gemini API key with no credit card required at aistudio.google.com"
    )
    if not api_key:
        st.info("👉 [Get a free Gemini API key here](https://aistudio.google.com/app/apikey)")
    
    st.divider()
    st.subheader("🎨 Clip & Layout Settings")
    num_clips = st.slider("Number of clips to extract", min_value=1, max_value=5, value=3)
    layout_mode = st.selectbox(
        "9:16 Layout Mode",
        options=["blur_backdrop", "center_crop"],
        format_func=lambda x: "✨ Dynamic Blurred Backdrop (Recommended)" if x == "blur_backdrop" else "✂️ Center Crop (Action/Speaker)"
    )
    use_gpu = st.checkbox("NVIDIA Hardware Acceleration (NVENC)", value=True)
    
    st.divider()
    st.markdown("**Engine Details:**")
    st.markdown("- **Brain:** Gemini 2.0 Flash")
    st.markdown("- **Video:** FFmpeg hardware-accelerated")
    st.markdown("- **Format:** 1080x1920 (9:16)")

# Main Workspace
url = st.text_input("🔗 Enter YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")

if "video_info" not in st.session_state:
    st.session_state.video_info = None
if "clips" not in st.session_state:
    st.session_state.clips = []
if "downloaded_video" not in st.session_state:
    st.session_state.downloaded_video = None
if "transcript" not in st.session_state:
    st.session_state.transcript = []

col_btn, col_empty = st.columns([1, 4])
with col_btn:
    analyze_btn = st.button("🚀 Analyze & Find Viral Clips", type="primary", use_container_width=True)

if analyze_btn:
    if not url.strip():
        st.error("Please enter a valid YouTube URL.")
    elif not api_key.strip():
        st.error("Please enter your Gemini API key in the left sidebar (it is completely free at aistudio.google.com).")
    else:
        video_id = extract_video_id(url)
        if not video_id:
            st.error("Could not parse YouTube video ID from the provided URL.")
        else:
            with st.spinner("🔍 Fetching video details & transcript..."):
                try:
                    info = get_video_info(url)
                    st.session_state.video_info = info
                    transcript = get_transcript(video_id)
                    st.session_state.transcript = transcript
                except Exception as e:
                    st.error(f"Error fetching video data: {e}")
                    transcript = []

            if not transcript:
                st.error("Could not retrieve a transcript for this video. Please make sure subtitles/closed captions are enabled on the video.")
            else:
                with st.spinner("🧠 AI Director analyzing hooks, story-arcs, and retention..."):
                    try:
                        clips = analyze_and_extract_clips(
                            transcript_items=transcript,
                            video_title=st.session_state.video_info.get("title", ""),
                            num_clips=num_clips,
                            api_key=api_key
                        )
                        st.session_state.clips = clips
                        st.session_state.downloaded_video = None # Reset
                        st.success(f"🎉 Successfully identified {len(clips)} high-retention clips!")
                    except Exception as e:
                        st.error(f"AI Director error: {e}")

# Display Video Overview
if st.session_state.video_info:
    info = st.session_state.video_info
    col1, col2 = st.columns([1, 3])
    with col1:
        if info.get("thumbnail"):
            st.image(info["thumbnail"], use_container_width=True)
    with col2:
        st.subheader(info.get("title", "Untitled"))
        st.markdown(f"**Channel:** {info.get('uploader')} | **Duration:** {int(info.get('duration', 0)//60)}m {int(info.get('duration', 0)%60)}s")

# Display Clips
if st.session_state.clips:
    st.divider()
    st.subheader(f"🔥 Viral Clip Candidates ({len(st.session_state.clips)})")
    
    output_dir = os.path.abspath("output")
    os.makedirs(output_dir, exist_ok=True)
    
    for idx, clip in enumerate(st.session_state.clips):
        with st.container(border=True):
            head_col1, head_col2 = st.columns([4, 1])
            with head_col1:
                st.markdown(f"### #{idx+1} {clip.get('title', 'Clip')}")
            with head_col2:
                score = clip.get('virality_score', 90)
                st.markdown(f"<span class='score-badge'>Viral Score: {score}/100</span>", unsafe_allow_html=True)
            
            # Hook overlay banner preview
            headline = clip.get('hook_headline', 'WAIT FOR IT')
            st.markdown(f"<div class='hook-banner'>📌 <b>Hook Headline Overlay:</b> <span style='color:#F59E0B;font-weight:bold;'>{headline}</span></div>", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            start_s = clip.get('start_time', 0)
            end_s = clip.get('end_time', 0)
            dur = clip.get('duration_seconds', end_s - start_s)
            
            with c1:
                st.markdown(f"⏱️ **Duration:** {dur:.1f}s (`{start_s:.1f}s` to `{end_s:.1f}s`)")
            with c2:
                st.markdown(f"🎯 **Hook:** *\"{clip.get('hook_quote', '')}\"*")
            with c3:
                st.markdown(f"🏁 **Payoff:** *\"{clip.get('punchline_quote', '')}\"*")
                
            if clip.get('power_words'):
                st.markdown(f"💥 **Dynamic Kinetic Words:** `{'`, `'.join(clip['power_words'])}`")
                
            st.markdown(f"💡 **AI Strategy:** {clip.get('reasoning', '')}")
            
            # Render Section
            clip_output_name = f"clip_{idx+1}_{int(start_s)}_{int(end_s)}.mp4"
            clip_output_path = os.path.join(output_dir, clip_output_name)
            
            render_col1, render_col2 = st.columns([1, 3])
            with render_col1:
                if st.button(f"🎬 Render 9:16 Short #{idx+1}", key=f"render_{idx}"):
                    # 1. Download source video if not already downloaded
                    if not st.session_state.downloaded_video or not os.path.exists(st.session_state.downloaded_video):
                        with st.spinner("📥 Downloading 1080p source video..."):
                            src_path = os.path.join(output_dir, f"source_{info.get('id', 'temp')}.mp4")
                            download_video(url, src_path, ffmpeg_path=get_ffmpeg_binary())
                            st.session_state.downloaded_video = src_path

                    # 2. Generate kinetic subtitles (.ass)
                    with st.spinner("✍️ Generating kinetic subtitles..."):
                        ass_path = os.path.join(output_dir, f"subs_{idx+1}.ass")
                        generate_ass_subtitles(
                            transcript_items=st.session_state.transcript,
                            clip_start=start_s,
                            clip_end=end_s,
                            output_ass_path=ass_path,
                            power_words=clip.get('power_words', [])
                        )

                    # 3. Render final 9:16 video
                    with st.spinner("🎥 Rendering 9:16 Vertical Short with GPU acceleration..."):
                        render_short_clip(
                            input_video=st.session_state.downloaded_video,
                            output_video=clip_output_path,
                            start_time=start_s,
                            end_time=end_s,
                            hook_headline=headline,
                            ass_subtitle_path=ass_path,
                            layout_mode=layout_mode,
                            use_gpu=use_gpu
                        )
                        st.success("✅ Short rendered successfully!")

            with render_col2:
                if os.path.exists(clip_output_path):
                    st.video(clip_output_path)
                    with open(clip_output_path, "rb") as f:
                        st.download_button(
                            label=f"⬇️ Download Short #{idx+1} (MP4)",
                            data=f,
                            file_name=clip_output_name,
                            mime="video/mp4",
                            key=f"dl_{idx}"
                        )
