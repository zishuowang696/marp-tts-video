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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural")
    parser.add_argument("--output", default="out/final.mp4")
    args = parser.parse_args()

    slides = split_slides((ROOT / "slides.md").read_text())
    texts = [tts_text(s, i) for i, s in enumerate(slides)]
    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    for old in out.glob("part*.mp4"):
        old.unlink()
    for old in out.glob("slide*.mp3"):
        old.unlink()

    run(["bunx", "@marp-team/marp-cli", "slides.md", "--images", "png",
         "--image-scale", "2", "--allow-local-files", "--output", "out/slide.png"])

    images = sorted(out.glob("slide.*.png"))
    if len(images) != len(slides):
        sys.exit(f"expected {len(slides)} images, got {len(images)}")

    ffmpeg = find_ffmpeg()
    edge_tts = find_edge_tts()
    parts: list[Path] = []

    for i, (image, text) in enumerate(zip(images, texts), 1):
        audio = out / f"slide{i}.mp3"
        part = out / f"part{i}.mp4"
        run([edge_tts, "--voice", args.voice, "--text", text, "--write-media", str(audio)])
        run([ffmpeg, "-y", "-loop", "1", "-framerate", "30", "-i", str(image),
             "-i", str(audio), "-c:v", "libx264", "-tune", "stillimage",
             "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p",
             "-shortest", str(part)])
        parts.append(part)

    concat = out / "list.txt"
    concat.write_text("".join(f"file '{p}'\n" for p in parts))
    run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-c", "copy", str(ROOT / args.output)])
    print(f"\nDONE: {ROOT / args.output}")


if __name__ == "__main__":
    main()
