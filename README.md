# marp-tts-video

Markdown → Marp 画面 → TTS 口播 → MP4。

## 依赖

- Bun（运行 `bunx @marp-team/marp-cli`）
- `edge-tts`（中文 TTS）
- `ffmpeg`

当前机器上 `edge-tts` 在 `~/.local/bin/edge-tts`，`ffmpeg` 可用 `imageio-ffmpeg` 提供：

```sh
python3 -m pip install --user edge-tts imageio-ffmpeg
```

## 跑

```sh
mkdir -p out
FF=$(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')

bunx @marp-team/marp-cli slides.md --images png --image-scale 2 \
  --allow-local-files --output out/slide.png

~/.local/bin/edge-tts --voice zh-CN-XiaoxiaoNeural \
  --text '同一份 Markdown，既生成画面，也生成口播。' \
  --write-media out/slide1.mp3

~/.local/bin/edge-tts --voice zh-CN-XiaoxiaoNeural \
  --text 'Marp 负责画面，TTS 负责声音，ffmpeg 把两者合成视频。' \
  --write-media out/slide2.mp3

"$FF" -y -loop 1 -framerate 30 -i out/slide.001.png -i out/slide1.mp3 \
  -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest out/part1.mp4
"$FF" -y -loop 1 -framerate 30 -i out/slide.002.png -i out/slide2.mp3 \
  -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest out/part2.mp4

printf "file '%s/out/part1.mp4'\nfile '%s/out/part2.mp4'\n" "$PWD" "$PWD" > out/list.txt
"$FF" -y -f concat -safe 0 -i out/list.txt -c copy out/final.mp4
```

## 现状

- 画面和音频能合成 MP4（样片：`out/sample.mp4`）。
- 口播文案目前是手动传给 TTS，还没有从 Markdown 的 speaker notes 自动提取。
- 下一步：每页写 `<!-- TTS: ... -->`，脚本按页提取、生成音频、按音频时长对齐画面。
