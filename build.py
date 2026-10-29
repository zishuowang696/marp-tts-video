#!/usr/bin/env python3
"""Build a video from Marp slides and TTS speaker notes.

Each slide must contain exactly one:
    <!-- TTS: text to speak -->
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def find_ffmpeg() -> str:
    if env := os.environ.get("FFMPEG"):
        return env
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    if p := shutil.which("ffmpeg"):
        return p
    sys.exit("ffmpeg not found; set FFMPEG or install imageio-ffmpeg")


def find_edge_tts() -> str:
    if p := shutil.which("edge-tts"):
        return p
    local = Path.home() / ".local/bin/edge-tts"
    if local.exists():
        return str(local)
    sys.exit("edge-tts not found; pip install --user edge-tts")


def split_slides(source: str) -> list[str]:
    m = re.match(r"(?s)^---\n.*?\n---\n(.*)$", source)
    body = m.group(1) if m else source
    return [s.strip() for s in re.split(r"(?m)^---\s*$\n?", body) if s.strip()]


def tts_text(slide: str, index: int) -> str:
    notes = re.findall(r"<!--\s*TTS:\s*(.*?)-->", slide, flags=re.S | re.I)
    if len(notes) != 1:
        sys.exit(f"slide {index + 1}: expected exactly one <!-- TTS: ... --> note")
    text = notes[0].strip()
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("`", "")
    return text


def srt_time_to_ass(t: str) -> str:
    h, m, rest = t.split(":")
    sec, ms = rest.split(",")
    return f"{int(h)}:{m}:{sec}.{ms[:2]}"


def srt_to_ass(srt_path: Path, ass_path: Path) -> None:
    raw = srt_path.read_text(encoding="utf-8").strip()
    blocks = re.split(r"\n\s*\n", raw) if raw else []
    events: list[str] = []
    for block in blocks:
        lines = [line for line in block.splitlines() if line.strip()]
        if len(lines) < 3:
            continue
        times = re.match(r"(.+?)\s*-->\s*(.+)", lines[1])
        if not times:
            continue
        text = "\n".join(lines[2:]).replace("{", "（").replace("}", "）")
        events.append(
            f"Dialogue: 0,{srt_time_to_ass(times.group(1))},"
            f"{srt_time_to_ass(times.group(2))},Default,,0,0,0,,{text}"
        )
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK SC,54,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3,0,2,60,60,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ass_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="slides.md")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural")
    parser.add_argument("--output", default="out/final.mp4")
    parser.add_argument("--no-captions", action="store_true")
    args = parser.parse_args()

    source = ROOT / args.input
    slides = split_slides(source.read_text())
    texts = [tts_text(s, i) for i, s in enumerate(slides)]
    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    for pattern in ("part*.mp4", "slide*.mp3", "slide*.srt", "slide*.ass", "slide.*.png"):
        for old in out.glob(pattern):
            old.unlink()

    run(["bunx", "@marp-team/marp-cli", str(source), "--theme-set", "themes",
         "--images", "png", "--image-scale", "1", "--allow-local-files",
         "--output", "out/slide.png"])

    images = sorted(out.glob("slide.*.png"))
    if len(images) != len(slides):
        sys.exit(f"expected {len(slides)} images, got {len(images)}")

    ffmpeg = find_ffmpeg()
    edge_tts = find_edge_tts()
    parts: list[Path] = []

    for i, (image, text) in enumerate(zip(images, texts), 1):
        audio = out / f"slide{i}.mp3"
        subtitles = out / f"slide{i}.srt"
        part = out / f"part{i}.mp4"
        run([edge_tts, "--voice", args.voice, "--text", text,
             "--write-media", str(audio), "--write-subtitles", str(subtitles)])
        cmd = [ffmpeg, "-y", "-loop", "1", "-framerate", "30", "-i", str(image),
               "-i", str(audio)]
        if not args.no_captions:
            ass = out / f"slide{i}.ass"
            srt_to_ass(subtitles, ass)
            cmd += ["-vf", f"subtitles=filename={ass}"]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-tune", "stillimage", "-r", "30", "-c:a", "aac",
                "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", str(part)]
        run(cmd)
        parts.append(part)

    concat = out / "list.txt"
    concat.write_text("".join(f"file '{p}'\n" for p in parts))
    run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-c", "copy", "-movflags", "+faststart", str(ROOT / args.output)])
    print(f"\nDONE: {ROOT / args.output}")


if __name__ == "__main__":
    main()
