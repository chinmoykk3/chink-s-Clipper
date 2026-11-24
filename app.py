import os
import glob
import json
import time
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

from core.downloader import get_video_info, extract_video_id, get_transcript, download_video
from core.ai_director import analyze_and_extract_clips
from core.subtitle_engine import generate_ass_subtitles
from core.video_processor import render_short_clip, get_ffmpeg_binary

# Load local environment variables if .env exists
load_dotenv()

st.set_page_config(
    page_title="Chink's Clipper",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Studio Theme with Modern Gradients)
st.markdown("""
<style>
    .brand-title {
        font-size: 2.6rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #FF3366, #FF6B35, #FFAA00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2px;
        letter-spacing: -0.5px;
    }
    .stat-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .stat-num {
        font-size: 2rem;
        font-weight: 800;
        color: #38BDF8;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .score-badge {
        background: linear-gradient(135deg, #10B981, #059669);
        color: white;
        padding: 5px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .hook-banner {
        background-color: #1E293B;
        border-left: 4px solid #F59E0B;
        padding: 12px 16px;
        border-radius: 6px;
        margin: 10px 0;
    }
    .feed-card {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.markdown("### ⚡ Chink's Clipper")
    st.caption("AI-Powered Short-Form Studio")
    st.divider()
    
    st.header("⚙️ API & Engine")
    env_key = os.getenv("GEMINI_API_KEY", "")
    api_key = st.text_input(
        "Google Gemini API Key",
        value=env_key,
        type="password",
        help="Get a 100% free Gemini API key with no credit card required at aistudio.google.com"
    )
    if not api_key:
        st.info("👉 [Get free Gemini key](https://aistudio.google.com/app/apikey)")
    
    st.divider()
    st.subheader("🎨 Studio Preferences")
    num_clips = st.slider("Clips to generate per video", min_value=1, max_value=5, value=3)
    layout_mode = st.selectbox(
        "Default Layout",
        options=["blur_backdrop", "center_crop"],
        format_func=lambda x: "✨ Dynamic Blurred Backdrop" if x == "blur_backdrop" else "✂️ Center Crop (Action/Speaker)"
    )
    use_gpu = st.checkbox("NVIDIA NVENC Hardware Acceleration", value=True)
    
    st.divider()
    st.markdown("**Hardware & Model Status:**")
    st.markdown("- **Brain:** Gemini 3.8 Flash")
    st.markdown("- **GPU:** NVIDIA GeForce RTX 4060")
    st.markdown("- **Format:** 1080x1920 (9:16 Vertical)")

# Helper: Load saved renders
def get_rendered_clips():
    output_dir = os.path.abspath("output")
    os.makedirs(output_dir, exist_ok=True)
    video_files = glob.glob(os.path.join(output_dir, "clip_*.mp4"))
    video_files.sort(key=os.path.getmtime, reverse=True)
    
    clips_data = []
    for f in video_files:
        meta_file = f.replace(".mp4", ".json")
        meta = {}
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as mf:
                    meta = json.load(mf)
            except Exception:
                meta = {}
        
        stat = os.stat(f)
        size_mb = stat.st_size / (1024 * 1024)
        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%b %d, %Y - %I:%M %p")
        
        clips_data.append({
            "path": f,
            "filename": os.path.basename(f),
            "size_mb": size_mb,
            "date": mod_time,
            "meta": meta
        })
    return clips_data

# Top Navigation Tabs
tab_home, tab_studio, tab_guide = st.tabs(["🏠 Home Feed & Gallery", "🎬 Studio (Create Clips)", "💡 Virality Playbook"])

# ==========================================
# TAB 1: HOME FEED & GALLERY
# ==========================================
with tab_home:
    col_head, col_action = st.columns([3, 1])
    with col_head:
        st.markdown('<h1 class="brand-title">⚡ Chink\'s Clipper</h1>', unsafe_allow_html=True)
        st.caption("Your personal command center for high-retention short-form content")
    
    rendered_clips = get_rendered_clips()
    
    # Top Stats
    st.markdown("<br>", unsafe_allow_html=True)
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-num">{len(rendered_clips)}</div>
            <div class="stat-label">Total Clips Rendered</div>
        </div>
        """, unsafe_allow_html=True)
    with sc2:
        avg_score = 0
        scores = [c['meta'].get('virality_score', 90) for c in rendered_clips if c.get('meta')]
        if scores:
            avg_score = int(sum(scores) / len(scores))
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-num">{avg_score or 95}%</div>
            <div class="stat-label">Avg. Virality Score</div>
        </div>
        """, unsafe_allow_html=True)
    with sc3:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-num">RTX 4060</div>
            <div class="stat-label">Hardware Acceleration</div>
        </div>
        """, unsafe_allow_html=True)
    with sc4:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-num">100% Free</div>
            <div class="stat-label">Local & Gemini Free Tier</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📱 Generated Shorts Gallery (Feed)")
    
    if not rendered_clips:
        st.info("👋 No clips generated yet! Switch over to the **🎬 Studio (Create Clips)** tab above, paste a YouTube link, and render your first viral short.")
    else:
        # Display clips in an Instagram/TikTok style 3-column mobile feed
        cols = st.columns(3)
        for i, clip_info in enumerate(rendered_clips):
            col = cols[i % 3]
            meta = clip_info.get("meta", {})
            title = meta.get("title", clip_info["filename"])
            headline = meta.get("hook_headline", "VIRAL HIGHLIGHT")
            score = meta.get("virality_score", 92)
            
            with col:
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    st.markdown(f"<span class='score-badge'>Viral Score: {score}/100</span>", unsafe_allow_html=True)
                    st.markdown(f"<div class='hook-banner'>📌 <b>{headline}</b></div>", unsafe_allow_html=True)
                    
                    st.video(clip_info["path"])
                    
                    st.caption(f"📅 {clip_info['date']} • 💾 {clip_info['size_mb']:.1f} MB")
                    
                    with open(clip_info["path"], "rb") as f:
                        st.download_button(
                            label=f"⬇️ Download Short",
                            data=f,
                            file_name=clip_info["filename"],
                            mime="video/mp4",
                            key=f"feed_dl_{i}",
                            use_container_width=True
                        )

# ==========================================
# TAB 2: STUDIO (CREATE CLIPS)
# ==========================================
with tab_studio:
    st.markdown('<h2 class="brand-title">🎬 Studio Creator</h2>', unsafe_allow_html=True)
    st.caption("Paste any YouTube video to extract high-retention 9:16 Shorts with dynamic kinetic subtitles.")

    url = st.text_input("🔗 Enter YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")

    if "video_info" not in st.session_state:
        st.session_state.video_info = None
    if "clips" not in st.session_state:
        st.session_state.clips = []
    if "downloaded_video" not in st.session_state:
        st.session_state.downloaded_video = None
    if "transcript" not in st.session_state:
        st.session_state.transcript = []

    c_btn, _ = st.columns([1, 4])
    with c_btn:
        analyze_btn = st.button("🚀 Analyze & Find Viral Hooks", type="primary", use_container_width=True)

    if analyze_btn:
        if not url.strip():
            st.error("Please enter a valid YouTube URL.")
        elif not api_key.strip():
            st.error("Please enter your free Gemini API key in the left sidebar.")
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
                    st.error("Could not retrieve a transcript for this video. Please make sure closed captions are available on the video.")
                else:
                    with st.spinner("🧠 AI Director evaluating hooks, story-arcs, and retention..."):
                        try:
                            clips = analyze_and_extract_clips(
                                transcript_items=transcript,
                                video_title=st.session_state.video_info.get("title", ""),
                                num_clips=num_clips,
                                api_key=api_key
                            )
                            st.session_state.clips = clips
                            st.session_state.downloaded_video = None
                            st.success(f"🎉 Identified {len(clips)} high-retention clips!")
                        except Exception as e:
                            st.error(f"AI Director error: {e}")

    # Video Info Preview
    if st.session_state.video_info:
        info = st.session_state.video_info
        c1, c2 = st.columns([1, 3])
        with c1:
            if info.get("thumbnail"):
                st.image(info["thumbnail"], use_container_width=True)
        with c2:
            st.subheader(info.get("title", "Untitled"))
            st.markdown(f"**Channel:** {info.get('uploader')} | **Duration:** {int(info.get('duration', 0)//60)}m {int(info.get('duration', 0)%60)}s")

    # Render Candidates
    if st.session_state.clips:
        st.divider()
        st.subheader(f"🔥 Viral Candidates Ready to Render ({len(st.session_state.clips)})")
        
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
                clip_meta_path = clip_output_path.replace(".mp4", ".json")
                
                render_col1, render_col2 = st.columns([1, 2])
                with render_col1:
                    if st.button(f"🎬 Render 9:16 Short #{idx+1}", key=f"render_{idx}"):
                        if not st.session_state.downloaded_video or not os.path.exists(st.session_state.downloaded_video):
                            with st.spinner("📥 Downloading 1080p source video..."):
                                src_path = os.path.join(output_dir, f"source_{info.get('id', 'temp')}.mp4")
                                download_video(url, src_path, ffmpeg_path=get_ffmpeg_binary())
                                st.session_state.downloaded_video = src_path

                        with st.spinner("✍️ Generating kinetic subtitles..."):
                            ass_path = os.path.join(output_dir, f"subs_{idx+1}.ass")
                            generate_ass_subtitles(
                                transcript_items=st.session_state.transcript,
                                clip_start=start_s,
                                clip_end=end_s,
                                output_ass_path=ass_path,
                                power_words=clip.get('power_words', [])
                            )

                        with st.spinner("🎥 Rendering 9:16 Short (NVENC GPU)..."):
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
                            # Save metadata for Home Feed
                            with open(clip_meta_path, "w", encoding="utf-8") as mf:
                                json.dump(clip, mf, indent=2)
                            st.success("✅ Short rendered & saved to your Home Feed!")
                            st.rerun()

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

# ==========================================
# TAB 3: VIRALITY PLAYBOOK
# ==========================================
with tab_guide:
    st.markdown("## 📈 The Viral Short-Form Playbook")
    st.markdown("""
    How **Chink's Clipper** beats the algorithms on YouTube Shorts, TikTok, and Instagram Reels:

    ### 1. The 3-Second Scroll-Stop Rule
    * If a viewer doesn't commit in the first 3 seconds, they swipe away.
    * Chink's Clipper cuts straight into the heart of the action and pins a bold, high-contrast **Hook Headline Overlay** directly across the top to capture peripheral vision.

    ### 2. Standalone Story Arc
    * Random 30-second cuts leave viewers confused.
    * Every clip chosen by our Gemini 2.0 Flash Director has a dedicated structure:
      * **Hook:** A bold assertion, question, or conflict.
      * **Tension/Context:** The explanation or build-up.
      * **Payoff:** The punchline, revelation, or closing takeaway.

    ### 3. Kinetic Subtitles & Power Words
    * Over 70% of viewers watch mobile shorts on mute or in noisy environments.
    * We group subtitles into rapid 3-4 word bursts with highlighted power words so the eyes never wander off the screen.
    """)
