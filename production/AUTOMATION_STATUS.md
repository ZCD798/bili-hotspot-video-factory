# Automation engineering status — 2026-10-18

## Completed and locally tested

- Preserved the prior Roadster V2 scripts as a legacy recipe. Added a topic-neutral pipeline using `story.json` and `assets_manifest.json` inputs, unfiltered timestamped Bilibili hotword capture, Commons image candidate search, explicit human rights-review gate, asset download/dimension/hash checks, strict claim/rights/path validation, isolated immutable run directories, Yunxi TTS, audio-derived subtitle timing, portrait photo scenes, Chinese burn-in captions and media QA.
- Captured a live Bilibili hotword snapshot at `2026-10-18T10:42:22+08:00`; `DeepSeek更新V4.1 Flash` was rank 4.
- Built a different-topic example with DeepSeek's official release page as the factual source and three Wikimedia Commons data-center images whose metadata identifies them as Public Domain or CC0. Each is labeled as generic illustrative infrastructure, not a DeepSeek site or event image.
- Generated one successful local run. It is stored in a unique `runs/<run-id>/` directory with story, source snapshot, rights manifest, audio, captions, font OFL license, QA report and MP4. Failed attempts remain in separate directories and were not overwritten.
- The prior local media QA passed: H.264 MP4, 1080×1920, 15 fps, 62.088 s, AAC mono 48 kHz, 8 subtitle cues, actual Yunxi voice, audio RMS check, full FFmpeg decode, and five-point visual-change sample. A contact sheet was visually reviewed; subtitles are legible after explicit fontconfig/libass registration.
- The initial attempts exposed two genuine issues (edge-tts missing/system CA certificate and libass not loading CJK glyphs); those failed run directories remain recorded as failed. The final separate run succeeded.

## Not completed / blocked

- GPT-based topic ranking, independent fact-check orchestration, oral script generation, and automated image search/license adjudication are not detached runner modules. The current example's editorial decisions and Commons rights review were prepared manually, then machine-validated. The pipeline fails closed on missing factual sources or license fields.
- The requested ChatGPT OAuth documents support eligible open-source/local apps and describe credential transfer to a self-hosted VM, but do not explicitly identify ephemeral GitHub-hosted Actions runners as eligible hosts. GitHub's runner is a GitHub-hosted VM, not a user self-hosted VM. Eligibility is therefore unconfirmed; this workflow does not implement or carry ChatGPT plan tokens and makes no model request.
- Google Drive/Gmail access in Work is not available to GitHub Actions. No Google OAuth client, refresh token, Actions secrets, Drive upload, Actions mail, owner-only link check, or seven-day MP4 deletion test exists.
- Google marks `gmail.send` as a sensitive scope. An external OAuth app left in Testing has refresh tokens that expire after seven days for non-profile scopes, so that state is not suitable for unattended daily use; In production status and the required Google verification are still needed.
- `.github/workflows/daily-video.yml` provides `workflow_dispatch` and `10 8 * * *` (16:10 Beijing). The schedule remains gated by `ENABLE_DAILY_PRODUCTION == 'true'` and defaults off. A workflow file or successful manual smoke test does not prove daily production; verify the action run history and delivery path before enabling the gate.
- GitHub Actions artifact retention is set to seven days for the small sanitized failure summary only. It does not retain or deliver a video.

## Minimum external setup before unattended production

1. Select/create a GitHub repository and put the code/workflow on the default branch. For a public repository, standard hosted runner minutes are free, but the video/source archive must not be uploaded as public Actions artifacts. GitHub scheduled starts can be delayed.
2. Obtain explicit confirmation that the planned ChatGPT OAuth host is eligible. If GitHub-hosted runners are not approved, use an already-owned, user-controlled self-hosted VM or a separately approved model route; no paid API key is introduced here.
3. Complete the Google OAuth setup in `DELIVERY_AUTH.md`, then implement and test private upload, Gmail send, access link and deletion with the Actions identity.
4. Run the manual production workflow and verify the full delivery/cleanup path. Only after that acceptance should the repository variable `ENABLE_DAILY_PRODUCTION` be turned on.
