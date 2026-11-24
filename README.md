# 🎬 AI Clipper Studio

Transform long-form YouTube videos into high-retention, viral **9:16 Shorts, Reels, and TikToks** — 100% free with hardware acceleration.

---

## 🌟 Key Differentiating Features
Unlike generic clippers (Opus Clip, Klap, etc.) that just slice random 30-second text chunks:
1. **Intelligent Story-Arc Hook Detection:** Evaluates transcript with Gemini 2.0 Flash to strictly require a 3-second scroll-stopping hook, escalation, and clean punchline resolution.
2. **Scroll-Stopper Headline Overlay:** Automatically generates punchy 3-5 word headline cards ("THE CODING TRICK", "NEVER DO THIS") shown for the first 3.5 seconds.
3. **Kinetic Typography:** Word-grouped captions with high-contrast outlines and colored highlights on dynamic power words.
4. **Cinematic 9:16 Framing:**
   - **Dynamic Blurred Backdrop:** Modern studio aesthetic with full 16:9 frame centered over an aesthetically blurred, scaled backdrop.
   - **Smart Crop:** Direct 9:16 center framing.
5. **NVIDIA Hardware Acceleration (NVENC):** Uses your RTX 4060 GPU for near-instant rendering.
6. **100% Free:** Uses Google AI Studio's free Gemini API tier and local FFmpeg.

---

## 🚀 Quick Start

### 1. Launch the App
Double-click `run.bat` or run in PowerShell:
```powershell
cd C:\Users\Asus\.gemini\antigravity\scratch\ai-clipper-studio
.\.venv\Scripts\streamlit run app.py
```

### 2. Enter Free Gemini API Key
- Get your free key at: [Google AI Studio](https://aistudio.google.com/app/apikey) (No credit card required).
- Paste it into the left sidebar in the web interface.

### 3. Paste Any YouTube Link & Click Analyze!
- Choose your preferred layout mode.
- Preview the AI-detected viral hooks and retention scores.
- Click **"Render 9:16 Short"** to produce mobile-ready MP4 clips.
