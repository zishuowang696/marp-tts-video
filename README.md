# marp-tts-video

Markdown → Marp 画面 → TTS 口播 → 抖音竖屏 MP4。

口播和字幕都来自每页的演讲备注：

```md
<!-- TTS: 这一页要念的话 -->
```

## 抖音默认参数

- 1080 × 1920（9:16）
- 30 fps
- H.264 High / yuv420p / faststart
- AAC 192k
- 字幕从 TTS SRT 转 ASS 烧录，底部安全区 260px
- 每页时长 = 该页口播时长

## 依赖

```sh
python3 -m pip install --user edge-tts imageio-ffmpeg
```

还需要 Bun（运行 `bunx @marp-team/marp-cli`）。

## 构建

```sh
./build.py
# 指定输入/输出
./build.py --input slides-vector.md --output out/vector.mp4
# 关闭字幕
./build.py --no-captions
# 指定声音
./build.py --voice zh-CN-YunxiNeural
```

输出：`out/final.mp4`。

## 结构

```text
slides.md          Markdown + TTS 备注
themes/douyin.css  1080×1920 主题
build.py           渲染/配音/字幕/合成
out/               中间文件与成片
```

## 注意

- 每页必须恰好一个 `<!-- TTS: ... -->`；
- 字幕字号 54、底部 MarginV 260，避免被抖音 UI 挡住；
- 想要更强节奏，拆页比加速更有效：一页一个观点。
