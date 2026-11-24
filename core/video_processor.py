import os
import subprocess
from typing import Optional
import imageio_ffmpeg

def get_ffmpeg_binary() -> str:
    """Return system ffmpeg if available, otherwise imageio_ffmpeg bundled binary."""
    # Check if ffmpeg in path
    try:
        res = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            return "ffmpeg"
    except Exception:
        pass
    return imageio_ffmpeg.get_ffmpeg_exe()

def render_short_clip(
    input_video: str,
    output_video: str,
    start_time: float,
    end_time: float,
    hook_headline: str = "",
    ass_subtitle_path: Optional[str] = None,
    layout_mode: str = "blur_backdrop", # "blur_backdrop" or "center_crop"
    use_gpu: bool = True
) -> str:
    """
    Renders high-retention 9:16 Short Video (1080x1920) with:
    - 9:16 Layout (Dynamic blurred backdrop or Smart center crop)
    - Hook Headline Overlay (first 4 seconds)
    - Styled Kinetic Subtitles (.ass)
    - Hardware-accelerated encoding (NVENC if supported)
    """
    ffmpeg_exe = get_ffmpeg_binary()
    duration = end_time - start_time
    os.makedirs(os.path.dirname(os.path.abspath(output_video)), exist_ok=True)

    # Escape subtitle path for ffmpeg filter syntax (handle Windows backslashes)
    sub_filter = ""
    if ass_subtitle_path and os.path.exists(ass_subtitle_path):
        clean_sub_path = ass_subtitle_path.replace("\\", "/").replace(":", "\\:")
        sub_filter = f",subtitles='{clean_sub_path}'"

    # Hook Headline Drawtext Filter (first 3.5 seconds)
    headline_filter = ""
    if hook_headline:
        clean_headline = hook_headline.replace("'", "").replace(":", "").replace('"', '').upper()
        headline_filter = (
            f",drawtext=text='{clean_headline}':"
            f"font='Arial':fontsize=56:fontcolor=yellow:bordercolor=black:borderw=4:"
            f"x=(w-text_w)/2:y=280:enable='between(t,0,3.5)'"
        )

    # Complex Filter depending on layout mode
    if layout_mode == "blur_backdrop":
        # Background: scale to 1080x1920 with crop and blur
        # Foreground: scale to 1080 width, maintain aspect ratio, overlay centered
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
            f"[0:v]scale=1080:-1[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[base]"
            f"{headline_filter}{sub_filter}"
        )
    else: # "center_crop"
        filter_complex = (
            f"[0:v]scale=-1:1920,crop=1080:1920[base]"
            f"{headline_filter}{sub_filter}"
        )

    # Choose encoder: test if NVENC is supported
    encoder = "libx264"
    if use_gpu:
        try:
            test_res = subprocess.run([ffmpeg_exe, "-h", "encoder=h264_nvenc"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if "h264_nvenc" in test_res.stdout:
                encoder = "h264_nvenc"
        except Exception:
            encoder = "libx264"

    cmd = [
        ffmpeg_exe,
        "-y",
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", input_video,
        "-filter_complex", filter_complex,
        "-c:v", encoder,
        "-preset", "fast",
        "-crf", "18" if encoder == "libx264" else "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_video
    ]

    print(f"Executing FFmpeg render: {' '.join(cmd)}")
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if process.returncode != 0:
        print(f"FFmpeg render error: {process.stderr}")
        # Fallback to software encoding if NVENC fails
        if encoder == "h264_nvenc":
            cmd[cmd.index("h264_nvenc")] = "libx264"
            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {process.stderr}")
        else:
            raise RuntimeError(f"FFmpeg failed: {process.stderr}")

    return output_video
