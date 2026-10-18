# Reusable daily hotspot video pipeline

This topic-agnostic media pipeline consumes story.json and assets_manifest.json and writes each attempt to a new runs/<task_id>/ directory. It uses the previously validated Microsoft Edge zh-CN-YunxiNeural voice at default speed; captions are timed from actual audio segment durations.

## Stages

1. collect_hotsearch.py captures public Bilibili hotwords and an Asia/Shanghai timestamp.
2. search_commons.py finds image candidates and records source and license fields. A person must review every license and mark rights_reviewed true.
3. fetch_licensed_assets.py downloads reviewed entries, verifies image decoding, and records hashes and dimensions. validate_inputs.py rejects missing rights/source fields, files, unsafe paths, and inconsistent references.
4. Topic choice, fact checking, and oral script are editorial inputs in story.json. ChatGPT-plan OAuth is not wired to GitHub runners pending eligibility confirmation.
5. make_audio.py generates Yunxi audio and derives captions from actual audio durations.
6. prepare_fonts.py registers OFL Noto Sans SC and saves the license per run.
7. render.py makes portrait scenes with photo motion and original graphics, burns in Chinese subtitles, and muxes AAC audio.
8. verify_media.py runs ffprobe, full decode, audio checks, and subtitle safe-area checks.
9. run_production.sh uses separate immutable run directories and records status and diagnostics.

Model-based editorial and private Google Drive/Gmail delivery still require separate authorized integrations. No generated video or credentials are uploaded by the local runner.

## Requirements

Python, edge-tts 7.3.1, Pillow, FFmpeg/FFprobe, a CJK font, and network access to Bilibili and Edge TTS. The checked-in sample snapshot is archival and does not represent today's ranking.

Run unit tests with: python -m unittest discover -s production/tests -v
