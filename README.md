# Prenew Creator Collaboration Copilot — discovery version

The original dependency-free HTML/CSS/JavaScript app is preserved. A Python standard-library server now provides YouTube discovery and validated CSV import. No package installation or build step is required. Local browser storage retains the existing campaign, demo pipeline, creator snapshots, reviews, notes and drafts.

## Exact local setup

```sh
git clone https://github.com/JessieXu959/Prenew_hackathon.git
cd Prenew_hackathon
cp -n .env.example .env
```

Open `.env` in an editor and set `YOUTUBE_API_KEY` to your own key. Enable **YouTube Data API v3** in its Google Cloud project and restrict the key to that API. This server makes server-side requests, so a browser-referrer-restricted key will not work. Never add the key to `dist/`, browser forms, commits or screenshots. `.env` is ignored, lives outside the served directory, and is not served by the server.

Stop any old `python3 -m http.server 4173` process with Ctrl+C, then:

```sh
python3 server.py
```

Open **http://127.0.0.1:4173/**. The same origin retains your previous browser data. Restart the server whenever `.env` changes. An environment variable, if set, takes precedence over `.env`. Optional `PORT` defaults to 4173. Without a key, CSV imports and all existing demo features still work, while YouTube shows an explicit setup error. No failed API request falls back to demo creators.

## What is real, imported, or fictional?

- **YouTube API tab:** official YouTube Data API v3 requests only. Channel identity, public subscriber counts, the videos that matched the search (up to three per channel, labeled) plus up to five latest public uploads, dates, metadata language clues, views, likes and comment counts come from the API. Hidden/missing values remain null. Public question-like comments load only when requested. No credentials were configured during implementation, so actual live retrieval has NOT been verified.
- **CSV imports tab:** Twitch, TikTok, Instagram and optional YouTube records supplied by the marketer. Every row requires a platform URL and provenance. These are uploader assertions, not API verification. No Twitch Helix integration is included because credentials were absent; CSV is the working second-source path.
- **Demo library:** the original 20 fictional profiles, explicitly segregated from live and imported results. Existing campaign setup, comparison and outreach flow remain available.
- **Outreach:** editable English templates. Approval changes a local status only. There is no email/message transport.

## Discovery and evidence

Choose market, language, niche, size and buyer/seller goal. Finland/Finnish and Germany/German have localized synonyms; France, Netherlands, Sweden and the UK are also supported. The query is visible and editable. For sellers, search terms emphasize resale/upgrades. Search uses region/language hints and videos from the last year, not audience location claims.

Suggested queries quote each multi-word alternative (`"halpa pelikone" | "budjetti pelitietokone"`) because YouTube's `|` operator otherwise binds single words. Each click fetches one page of up to 25 matching videos, deduplicates channel IDs, keeps each channel's matched videos as evidence, gets channel metadata in one batch, filters by known channel size and enriches candidates through their uploads playlists and video statistics. Channels with known fewer than 100,000 followers are grouped first and then ranked by evidence fit. Nano is <10k, micro is 10k–100k, mid is 100k–500k. A size filter excludes unknown-size channels rather than assuming they are small. Search results are not an exhaustive census; use more localized queries and subsequent result pages if results are sparse.

Five adjustable factors: keyword relevance across matched and recent video titles/descriptions (keywords match at word starts, long stems also inside compounds, so `latest` no longer counts as `test`); declared language metadata; posting recency; views relative to subscriber count; and available public engagement. Unknown factors are excluded from the weighted mean and evidence coverage is displayed. All-zero weights yield no score. These are transparent triage heuristics, not trust scores, audience demographic estimates or campaign predictions. One supplied imported video is a narrow evidence sample. Shorts/streams/long videos are not normalized. Subscriber counts are as reported by YouTube and may be rounded.

Trust review links to original content and asks a human to inspect benchmark methods, trade-offs, sponsorships and questions. The app has not watched the video. Comment sampling filters question marks and length in up to 20 top-level comments; that does not establish substance or representativeness. No honesty or audience claims are inferred from likes.

Audience geography stays unverified unless a CSV supplies both a country and an audience source URL. Even then it is labeled an uploader-supplied claim, not independent verification. Prices, fees, contact details, demographics, willingness and performance promises are never inferred.

## Working CSV import

Download `creator-template.csv` in the UI, fill with real records, and upload or paste it. UTF-8, quoted commas/newlines and BOM are supported. Maximum 500 rows / 1 MB. The whole import is rejected with row errors if any row is invalid; blank numeric values remain unknown. The template has headers only so it cannot be mistaken for real creator data.

Required columns: `name,platform,source_url,provenance`.

Optional: `country,market,language,topic,followers,video_url,video_title,video_description,published_at,views,likes,comments,audience_country,audience_source`.

Use `FI`, `DE`, etc. for discovery market and `fi`, `de`, etc. for language. `country` describes supplied creator location, not audience geography. Dates are ISO 8601; numeric counts are nonnegative integers. `video_title` is required with `video_url`. URLs must be http(s); the creator URL must belong to the stated platform. Source URLs are not fetched during import. One row supplies one example video; repeated profile URLs within a file are deduplicated. Reimporting the same platform/profile path updates the record and preserves its saved notes/status. Different YouTube handle/channel aliases are not automatically resolved across imports and API data.

## Actionable shortlist

Save a candidate, set Reviewing / Accepted / Rejected, and add notes. Rejection invalidates outreach approval; reopen the review before approving outreach. Export all saved entries or an individual candidate to CSV with source URLs, provenance, timestamps, evidence titles/dates/URLs, market/language, score components, scoring configuration, review notes, unknowns, collaboration angle and outreach status. CSV cells are quoted and spreadsheet formula prefixes are neutralized. Rejected records remain in the export with their decision for auditability.

One local campaign is supported. Changing the campaign brief clears previous outreach drafts/approvals and resets outreach status, as the UI explains. Discovery filter changes rerank the current evidence; they do not automatically launch another API search. Existing notes remain. API snapshots saved in browser storage may become stale: inspect the displayed collection date and rerun searches.

## Cache, quota and errors

- Thirty-minute in-memory cache for each upstream request and complete search result; cached result timestamps are preserved. Restarting clears caches.
- At most 40 uncached search requests and 1,000 total API calls per UTC day **per server run**. This is a conservative app guard, not an accounting of Google quota units; consult the Cloud console for actual project quotas. Restarts reset the guard.
- Each candidate may require one playlist request and one video-statistics request, in addition to the search and batched channels lookup. No background searches, auto-pagination, automatic retries or eager comment fetching.
- API-disabled/key-restriction/quota-denied, network, invalid query, empty-result and missing-key states are explicit. Secrets and upstream request URLs are not logged or returned.
- Server binds to loopback, rejects foreign Host/Origin requests and serves only an allowlist of public files. This is a single-user prototype, not a production authenticated service.

## 60-second demo

With your key configured (results depend on current YouTube data):

1. **0–15s:** select Finland, Finnish, Budget gaming, Nano or Micro. Show `halpa pelikone | budjetti pelitietokone`, then Search YouTube. Point out actual API provenance and unverified audience geography.
2. **15–30s:** open a returned small creator. Show subscriber count, dated linked videos, matched keywords, language clues and unknown engagement fields. Inspect the source; do not declare trust from the score. If that page contains no small channel, widen to all sizes or load another page; do not claim a result that did not appear.
3. **30–45s:** save, mark Reviewing and write one concrete verification question about testing, condition, warranty or value. Export the shortlist.
4. **45–60s:** switch to Germany/German. Show `günstiger Gaming PC | Budget Gaming PC` and run the same search. Compare evidence and coverage rather than raw follower counts across markets.

Without credentials, steps 1 and 4 demonstrate localization and the explicit missing-key state, not a real search. Use your own sourced CSV to demonstrate a real small creator; or the separate Demo library to demonstrate fictional workflow only. No real small creator was verified during this run.

## Verification

```sh
python3 -m unittest discover -s tests -v
node tests/core.test.mjs
```

Node is only needed for JavaScript tests, not to run the app. `node --check dist/app.js`, `dist/discovery.js`, `dist/research-core.js`, and `dist/examples.js` check syntax. See `VERIFICATION.md` for the actual checks and remaining limitations.

## Repository layout

- `server.py`: local API server, server-side YouTube integration, cache and CSV validation.
- `dist/`: browser application, discovery UI, demo library and styles.
- `tests/`: backend and browser-logic checks using synthetic fixtures only.
- `.env.example`: credential and port template; the real `.env` remains ignored.
- `creator-template.csv`: header-only import template.
- `VERIFICATION.md`: checks completed and known limitations.
- `Finnish_companies_5-10M.json`: pre-existing repository data, preserved unchanged.

## Official references

- [YouTube search](https://developers.google.com/youtube/v3/docs/search/list)
- [Channels](https://developers.google.com/youtube/v3/docs/channels/list)
- [Uploads playlist items](https://developers.google.com/youtube/v3/docs/playlistItems/list)
- [Videos and statistics](https://developers.google.com/youtube/v3/docs/videos/list)
- [Comment threads](https://developers.google.com/youtube/v3/docs/commentThreads/list)
- [Twitch Helix](https://dev.twitch.tv/docs/api/reference) — not integrated in this version
