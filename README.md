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

Choose language, niche, size and buyer/seller goal. Finnish and German have localized synonyms; French, Dutch, Swedish and English are also supported. The query is visible and editable. For sellers, search terms emphasize resale/upgrades. Search uses YouTube language ranking plus a filter on declared video/channel language metadata, and videos from the last year. Country is not sent to YouTube and is not used to include or exclude creators.

