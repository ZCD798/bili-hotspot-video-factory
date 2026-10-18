# bili-hotspot-video-factory

## Repeatable video production

The topic-neutral producer, workflow, example story, source snapshot, rights manifest, and local validation tests are in [production/README.md](production/README.md). Use **Actions → Daily Bilibili hotspot video → Run workflow → local-smoke** to validate the runner. The workflow fetches openly licensed Commons example images at runtime; it does not commit or upload the resulting MP4.

The scheduled trigger is present at 16:10 Beijing time, but formal daily production remains disabled unless the repository variable `ENABLE_DAILY_PRODUCTION` is explicitly set to `true`. The production job still fails closed until eligible model access and separate Google delivery authorization are implemented and accepted. A manual smoke run does not prove unattended production.
