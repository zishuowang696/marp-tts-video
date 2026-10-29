# marp-tts-video

Markdown → Marp 画面 → TTS 口播 → MP4。

口播文案来自每页的演讲备注，不再手动传文本：

```md
<!-- TTS: 这一页要念的话 -->
```

## 依赖

- Bun（`bunx @marp-team/marp-cli`）
- `edge-tts`
- `ffmpeg`

```sh
python3 -m pip install --user edge-tts imageio-ffmpeg
```

## 构建

```sh
./build.py
# 或指定声音/输出
./build.py --voice zh-CN-XiaoxiaoNeural --output out/final.mp4
```

流程：

1. 解析每页 `<!-- TTS: ... -->`
2. Marp 导出 PNG
3. edge-tts 逐页生成 mp3
4. ffmpeg 按音频时长合成并拼接
5. 输出 `out/final.mp4`

## 约束

- 每页必须恰好一个 `TTS` 备注；
- 音频按页生成，页面时长等于该页口播时长；
- 需要更复杂的转场/字幕/背景音乐时，再在 ffmpeg 层扩展。
