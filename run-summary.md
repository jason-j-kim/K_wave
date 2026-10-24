# Run summary: r/ClaudeAI scrape

- **Source:** https://www.reddit.com/r/ClaudeAI/ (default "Best" feed, logged out)
- **Checked at:** 2026-10-24T09:18:52Z
- **Status:** `ok`. The run finished. Reddit served the pages and showed no robot check, sign-in wall or rate limit.
- **Tool:** Playwright Chromium (pre-installed) in a cloud container, through the environment proxy. ego (lite) was not installed because it does not run on Linux. The data is not in an ego (lite) Space.
- **Limits:** up to 50 posts from the feed; the first 10 threads opened; up to 50 rendered comments per thread.
- **Recorded:** 1 status row, 50 posts, 268 comments in `reddit-data.csv`.
- **Script:** `scrape-reddit.js` (`node scrape-reddit.js reddit-data.csv`).

## Notes on the data
- The 2 pinned community highlights and promoted posts were skipped. Duplicates were removed.
- `text` for a post is the feed preview. For the 10 opened threads it is the full body. 22 posts have `not displayed` because they are link, image or video posts with no text body.
- Comments are the ones rendered on first load plus a few scrolls. Collapsed replies and "more replies" were not expanded. None of the 10 threads hit the 50-comment cap.
- 13 comments have `text = not displayed`: they are image or GIF-only comments, or deleted (`[deleted]`).
- `date_or_relative_time` is the ISO timestamp from the page. `note` gives the comment depth (0 = top level).
- `score` is the vote count Reddit showed when the page was loaded.

## Previous attempt
The earlier run (commit 91409b0) was blocked by the environment's network policy (proxy 403 on www.reddit.com). That restriction no longer applies.
