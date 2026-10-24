# Run summary — r/ClaudeAI scrape

- **Source:** https://www.reddit.com/r/ClaudeAI/
- **Checked at:** 2026-10-24T09:07:15Z
- **Status:** `blocked:network_policy_denied`. The run did not finish.
- **Tool:** Playwright Chromium in a cloud container. ego (lite) can't be used here because it only runs on macOS/Windows. You approved this fallback, so the data is not recorded in an ego (lite) Space.
- **Limits planned:** up to 50 posts from the feed; up to 10 threads opened; up to 50 rendered comments per thread.
- **Recorded:** 0 posts, 0 comments. `reddit-data.csv` holds a single `row_type=status` row.

## What happened
The cloud environment's outbound network policy refused the connection to `www.reddit.com`. The proxy answered 403 to CONNECT, and Chromium showed `ERR_TUNNEL_CONNECTION_FAILED`. Reddit never served a page, so this is not a Reddit sign-in wall, CAPTCHA, or rate limit. It is not an empty feed either.

## Needs your review
- Allow `www.reddit.com` (and `reddit.com`) under the environment's Network access setting, then re-run. Or run the task locally with ego (lite).
- If the rerun works from this datacenter IP, Reddit may still show a robot check. If it does, the run will stop and record it.
