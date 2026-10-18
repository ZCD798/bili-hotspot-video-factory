# External delivery authorization plan (not configured)

GitHub Actions does not inherit the signed-in Google Drive/Gmail connectors available in ChatGPT Work. A separate Google OAuth grant for the Actions application is required.

## Least necessary scopes

- Drive upload, read back the newly created file metadata/link, and delete that same app-created file for seven-day cleanup: `https://www.googleapis.com/auth/drive.file`. Google classifies this as a non-sensitive Drive scope; `files.delete` accepts it. The uploader must not create public permissions; keep the MP4 owner-only and send the owner-only Drive URL to the confirmed address.
- Send one completion/failure email: `https://www.googleapis.com/auth/gmail.send`. This is a sensitive Gmail scope and Google says sensitive-scope OAuth verification may apply. No Gmail read, modify, or full-mailbox scope is needed.

## Authorization and secret setup still required

1. In a Google Cloud project controlled by the account owner, enable Drive API and Gmail API and configure an OAuth consent screen. Google documents that an External app in Testing gets a refresh token that expires after seven days when requesting non-profile scopes; that is unsuitable for daily unattended runs. For durable use, move the app to In production and complete the verification Google requires for the sensitive `gmail.send` scope. A temporary Testing token can only be used for a one-off/manual test.
2. Create an OAuth client for the local authorization flow, request the two scopes above with offline access, and authorize the account owner after the app has the required publishing/verification state. The resulting client secret and refresh token belong in GitHub Actions encrypted Secrets; never put them in the repository, workflow output, artifacts or logs.
3. Configure `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, and `GOOGLE_REFRESH_TOKEN` as repository Secrets. Use the owner’s confirmed recipient from a protected repository variable; do not commit a personal email address or expose it in logs. The future delivery code must mask tokens, upload privately, read back the Drive file ID and owner-only link, send the mail, and validate both API results.
4. Seven-day expiry requires storing `file_id` and `expires_at` in a durable task ledger, scheduling a cleanup workflow, deleting only expired IDs with `drive.file`, and verifying the deletion response. Until that delete test succeeds, no seven-day MP4 retention promise is valid.

None of these OAuth grants, Secrets, uploads, emails, or cleanup runs has been created or tested by this local production task.
