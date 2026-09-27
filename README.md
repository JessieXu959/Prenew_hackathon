# Prenew Creator Collaboration Copilot

Discover relevant creators from live YouTube evidence, review their fit, and export a shortlist. The existing dependency-free app, fictional demo library, local shortlist, comparison, CSV import and optional outreach drafts are preserved. No messages are sent by this prototype.

## Run locally

```sh
git clone https://github.com/JessieXu959/Prenew_hackathon.git
cd Prenew_hackathon
cp -n .env.example .env
# Set YOUTUBE_API_KEY in .env, then:
python3 server.py
```

Open http://127.0.0.1:4173/. Enable YouTube Data API v3 for your key. The key stays on the server; `.env` is ignored and is outside the public-file allowlist. Do not put a key in `dist/`, screenshots or commits. Restart after changing `.env`. Optional `PORT` defaults to 4173; environment variables take precedence over `.env`. There is no package installation or build step. Node is needed only for JavaScript tests.

## Discover and inspect

1. Choose a **target country / market**, language, niche and optional size or metric limits. Finland, Germany, France, the Netherlands, Sweden and the UK are supported with localized queries. Changing market selects its default language; you can then change the language separately.
2. Edit the query or use the localized suggestion, then **Search YouTube**. One click requests one page of up to 25 video matches. A region or language search hint does not establish creator or audience location.
3. Inspect the creator's declared country and its source, content language evidence, subscribers, recent average views, niche/game/hardware labels, and any explicit public contact. Missing information is shown as **Unknown** or **No public contact found**.
4. Open linked videos, save to the shortlist, record a review and notes, then export CSV. Scores are transparent triage heuristics, not trust judgments or performance promises.

New workspaces default both numeric limits to 0 (disabled), so small creators are discoverable. Existing saved filter settings are preserved. Positive limits retain the existing **greater than** behavior and exclude unknown metrics. Prenew's typical YouTube ranges of 50k–250k subscribers / 20k–100k views and TikTok 4k+ followers are reference examples, not eligibility thresholds.

## Conservative country and language checks

Live results must have a channel-declared country equal to the selected market. Missing or mismatched country is excluded. Up to five latest public, non-ongoing uploads are examined: at least three must be available, at least two must have matching audio/metadata language, and no inspected video or channel language may contradict the selected language. Locale variants such as `de-DE` match `de`.

Audio language and title/description metadata language are retained separately. Titles and description excerpts are visible with source links for human review. An English game title, one old search hit, a channel tag alone, or a high score cannot override the gate. Text-only language inference and a “needs verification” candidate bucket are deliberately not implemented: this version retains a strict path and may miss valid multilingual or poorly annotated creators. It does not listen to videos or transcribe speech.

The browser also enforces country/language checks on saved live results. Changing market does not expose results from the previous market. Niche fit uses sampled uploads published within 90 days; old search-only matches cannot make unrelated current content pass. Imported records remain uploader claims and are separately labeled; known country/language contradictions are hidden.

**Target market, channel-declared country, content language, and verified audience country are separate.** Audience geography stays unknown. Imported audience claims and source URLs are exported separately and are never upgraded to independent verification.

## Recent average views

The server retrieves up to **50 latest public uploads**, plus up to three search matches retained as discovery evidence. Video-detail requests are batched in groups of at most 50.

- Use actual public view counts for uploads published in the last **30 days**.
- If fewer than **three measured uploads** are available, use a **90-day fallback**.
- If that sample still has fewer than three videos, the average is **Unknown / insufficient sample**.
- Search-only matches, future publications, ongoing/upcoming broadcasts, missing dates and missing view counts do not enter the average. Zero observed views remain zero.
- Cards, details, comparison and CSV use the same measured result. They include publication window, sample size, timestamp and any sample cap / missing-count flags. Details and CSV identify the included videos and counts.
- This is the mean **lifetime public view count of videos published in the window**, not the views gained by the channel during those days. Shorts, completed streams and long videos are mixed and are not normalized. If 50 uploads do not cover the window, the latest-50 sample is explicitly labeled; it is not advertised as a complete channel average.

Older saved snapshots without this measurement show Unknown and require a new search. One imported example video is not a measured 30/90-day average. Set the view limit to 0 to review such imports.

## Evidence, contact and ranking

Niche/game/hardware labels use recent video **titles**, with example-video links. Keyword matching is heuristic and can miss topics or be ambiguous. Topic scoring also uses descriptions. The existing adjustable topic, recency, views-relative-to-size and public-engagement weights are retained; language is an eligibility check with no ranking weight. Unknown score factors are excluded from the weighted mean, all-zero weights yield no score, and evidence coverage is displayed. Comparison likes/comments and engagement remain averages of supplied evidence videos, with their own sample counts.

A public contact is included only when a contact-labelled line of the public **channel description** explicitly contains an email or HTTP(S) contact link. The source is retained. Email addresses are never constructed; ownership, availability and willingness are not verified. A hidden About-page business email or an unlabelled website may remain undiscovered. No scraping, contact enrichment or sending was added.

Human review still covers methods, trade-offs, sponsorships, conflicts and audience questions. Comment retrieval remains on demand. The app has not watched the source videos. Fees, demographics, exclusivity and collaboration interest are unknown.

## CSV import and export

Imports support YouTube, TikTok, Twitch and Instagram with a required platform source URL and provenance. UTF-8, BOM and quoted fields are supported; maximum 500 rows / 1 MB. Validation is atomic. Same-profile duplicates update the stored record while preserving its local review. No TikTok API was added. Demo creators remain fictional and separate from both live results and imports.

Download `creator-template.csv`. Required columns: `name,platform,source_url,provenance`. Optional columns: `country,market,language,topic,followers,video_url,video_title,video_description,published_at,views,likes,comments,audience_country,audience_source`. Use country codes such as `FI` / `DE` and language codes such as `fi` / `de`. Counts are nonnegative integers; blanks remain unknown. One row provides one example video, not a time-window average. Source URLs are not fetched during import.

Shortlist CSV now includes country/source; target market; content and search languages; language evidence/source links; subscribers; recent average views/window/sample/check date; included video URLs/counts; niche/game/hardware and evidence links; public contact/source; review notes; missing-data flags; scoring configuration; and existing outreach status. Audience claims are separate from verified audience country. Cells are quoted, UTF-8 BOM is retained, and spreadsheet formula prefixes are neutralized.

One local campaign is supported. Changing its brief resets existing outreach drafts/approvals as explained in the UI. Approving a draft changes local status only. Browser snapshots may become stale: inspect timestamps and rerun discovery.

## Cache, quota and security

- 30-minute in-memory API/search cache. Complete cached searches preserve snapshot timestamps; market is included in the cache identity.
- At most 40 uncached searches and 1,000 total API calls per UTC day **per server run**. This is an app request guard, not Google quota-unit accounting. Restarting resets it.
- No background search, automatic pagination/retries or eager comments. Enrichment adds one uploads request and up to two video-detail requests per country-matching channel.
- Missing key, denied access, quota, network, empty-result and invalid-input states remain explicit. Failed requests never substitute fictional creators.
- The server binds to loopback and checks Host/Origin. Only an allowlist of public files is served. Upstream URLs and credentials are not returned or logged. This is a local prototype, not an authenticated production service.

## Verification and demo

```sh
python3 -m unittest discover -s tests -v
node tests/core.test.mjs
node tests/discovery.test.mjs
node --check dist/app.js
node --check dist/discovery.js
node --check dist/research-core.js
node --check dist/examples.js
```

See [VERIFICATION.md](VERIFICATION.md) for actual live checks, exact creator/video URLs and limitations, and [CHANGES.md](CHANGES.md) for the English change report and 60-second discovery/export demo.

## Repository layout

- `server.py`: local API, YouTube retrieval/cache, CSV validation and public-file server.
- `discovery_evidence.py`: strict recent-language assessment, publication-window averages and explicit public contact extraction.
- `dist/`: existing browser app, discovery, comparison, styles and fictional demo.
- `tests/`: synthetic regression fixtures; never injected into live results.
- `.env.example`: setup template; real `.env` is ignored.
- `creator-template.csv`: header-only import template.
- `Finnish_companies_5-10M.json`: pre-existing repository data, unchanged.

## Official API references

[Video fields and statistics](https://developers.google.com/youtube/v3/docs/videos), [channel metadata](https://developers.google.com/youtube/v3/docs/channels), [uploads pagination](https://developers.google.com/youtube/v3/docs/playlistItems/list), [search hints](https://developers.google.com/youtube/v3/docs/search/list), and [comments](https://developers.google.com/youtube/v3/docs/commentThreads/list).
