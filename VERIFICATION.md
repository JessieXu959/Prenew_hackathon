# Verification — 27 September 2026

Base commit `94dfad9`, branch `codex/discovery-evidence-market-accuracy`. Verification used the configured server-side YouTube key without printing it. Public API responses were inspected; no synthetic fixture was substituted into a live result. The local verification server used port 4187 to avoid replacing any existing instance on 4173.

## Automated checks

- `python3 -m unittest discover -s tests -v`: **22 passed** (9 existing backend checks updated for the stricter evidence contract; 13 additional evidence regressions).
- `node tests/core.test.mjs`: passed, including score/unknown handling, localization, CSV formula protection, canonical average consistency, niche evidence, language contradictions and required export columns.
- `node tests/discovery.test.mjs`: passed, including strict language/country filtering, BR/CN/JP regression fixtures for Sweden, previous-market isolation, minimum-metric boundaries, unverified imports, ranking, current-niche evidence and required UI fields.
- JavaScript syntax checks: `dist/app.js`, `dist/discovery.js`, `dist/research-core.js`, `dist/examples.js`.
- Python compilation: `server.py`, `discovery_evidence.py`.
- HTTP smoke checks: status 200; `.env`, `server.py` and `discovery_evidence.py` blocked with 404; unsupported market rejected with 400; foreign-Origin import rejected with 403. `.env` remained ignored, and the staged diff was checked for the configured key before commit.

Synthetic tests additionally cover 30-day samples, 90-day fallback/boundary, fewer than three videos, missing dates/counts, observed zero counts, old search-hit exclusion, future/live exclusion, latest-50 truncation, separate audio/metadata conflicts, cache market isolation, unsupported markets, explicit-contact extraction, missing-key and redacted upstream errors, rate-limit cooldown, deduplication, pagination and atomic CSV validation.

## Real searches and manual evidence review

All searches used `all` creator sizes. Final niche review used numeric limits disabled (0), allowing overlooked small creators. These are point-in-time results, not permanent expected results.

| Market / query | Country/language survivors | Exclusions before niche filtering | Relevant displayed result(s) |
| --- | --- | --- | --- |
| Finland / `pelikone`, Gaming | 3 | 3 unknown country, 2 language conflict | Napalmi |
| Germany / `"günstiger Gaming PC" \| "Budget Gaming PC"`, Budget gaming | 3 | 14 country mismatch, 4 unknown country | Papa Oki, HardwareDealz |
| Sweden / `speldator`, Gaming | 2 | 21 country mismatch, 1 unknown country, 1 language conflict, 1 insufficient language | Teknikhype |

The original narrow Finland budget suggestion was also tested. It returned one metadata-qualified channel with mixed personal content and about 105 average views. It was not selected as the demo example. The broader `pelikone` query plus current-niche filtering found a more useful small-market example. Changing a query does not relax the country/language gate.

Manually inspected the top returned creators' most recent five titles and descriptions plus recent niche evidence:

- [Napalmi — Finland](https://www.youtube.com/channel/UC3MbBJ8gywAevQF4PgfeTWg): 1,940 reported subscribers; five latest uploads had matching Finnish audio/metadata tags. General computer-help content mixed with current PC-build and hardware content. Example: [Ryzen 7 / RTX 5070 Ti PC build](https://www.youtube.com/watch?v=869IDdrHL74), [RTX 5070 Ti unboxing](https://www.youtube.com/watch?v=FQW-rndDrBU). A May search hit remains visible but is excluded from current niche scoring and the view average. Creator/business conflicts still require review.
- [Papa Oki — Germany](https://www.youtube.com/channel/UCbr16iFtdirWf8UpMpEEEqw): 3,130 subscribers; five inspected uploads had matching German metadata, covering used graphics cards, SSD prices and budget PC builds. [Recent used-GPU video](https://www.youtube.com/watch?v=OFfEXLG7Gv0), [SSD pricing video](https://www.youtube.com/watch?v=3DUtGJqRVa4).
- [HardwareDealz — Germany](https://www.youtube.com/channel/UCHj7VElFb0_sxhI5KHduM7A): 866,000 subscribers; five inspected uploads had matching German metadata, with PC tests/builds/giveaways. [2016 gaming PC test](https://www.youtube.com/watch?v=sHR-Q0LC5B8), [PC giveaway](https://www.youtube.com/watch?v=UsVl1IAfRqg). Larger than Prenew's typical range, but not arbitrarily excluded.
- [Teknikhype — Sweden](https://www.youtube.com/channel/UCdbJCKT87le87K3EvICmWXA): 3,020 subscribers; five inspected recent uploads had matching Swedish metadata and gaming/PC topics. 22 measured uploads in 30 days, averaging 4,882.6364 views. RBN Tech passed country/language checks but had only one measured upload in 90 days and lacked the selected current Gaming keyword evidence, so it was not shown for that final niche.

Language was checked from API metadata and visible text evidence; spoken audio was not independently verified. No unrelated-country creator was displayed in these inspected result sets. Synthetic regressions explicitly demonstrate that BR/CN/JP channels and Portuguese/Chinese/Japanese language conflicts cannot pass Sweden selection even with high metrics.

## Average-view and CSV cross-check

The export was produced by the same `shortlistCSV` function used by both UI export buttons. A separate Python `csv.DictReader` check recomputed the sample from publication timestamps and each linked video's raw view count, then compared the mean, sample size, contributing URLs, country and unknown audience field against the exported row.

| Creator | Snapshot (UTC) | Publication window | Videos | Sum of video views | Exact exported mean |
| --- | --- | --- | ---: | ---: | ---: |
| Napalmi | 2026-09-27 07:36:47 | 30 days | 48 | 89,940 | 1,873.75 |
| Papa Oki | 2026-09-27 07:34:42 | 90-day fallback | 6 | 5,413 | 902.1666666666666 |
| HardwareDealz | 2026-09-27 07:34:44 | 30 days | 22 | 2,296,363 | 104,380.13636363637 |

All three matched exactly. The UI rounds to one decimal for readability; CSV retains precision. Example raw linked records: Napalmi [4TQiZNeqUSM](https://www.youtube.com/watch?v=4TQiZNeqUSM) = 1,771 views and [OMG2Q7Wqz8I](https://www.youtube.com/watch?v=OMG2Q7Wqz8I) = 244 at the snapshot. These public counts may subsequently change.

No public contact satisfying the explicit channel-description rule was found for these three examples. Their CSV rows say **No public contact found**. This does not mean the creator has no contact route elsewhere. Verified audience country is **Unknown** in all rows.

## Browser flow

Verified the actual locally served UI, not only generated HTML:

- Finland/Finnish/Gaming query `pelikone` and turning off the minimum-view filter displayed Napalmi.
- Creator details showed country/source, content language, audience unknown, measured average/window/count/check date, linked niche evidence, and individually marked view-sample videos.
- Saved Napalmi, set Reviewing, added notes about mixed formats/audience/conflicts; the shortlist and review survived a full reload.
- Individual candidate CSV and full-shortlist CSV export controls executed.
- Switching to Germany selected German automatically. The localized budget query displayed Papa Oki and HardwareDealz after current-niche filtering.
- Comparing the two German creators showed consistent view means/counts/windows and separate country/language/audience/contact fields. Layout was visually inspected.
- No browser errors/warnings were recorded during the checked discovery/review/export flow. Existing outreach code and fictional demo data were unchanged; the complete outreach flow was not re-exercised in this update.

## Known limits

- No new Estonia or Hungary support, provisional candidate bucket, text-language classifier, speech recognition or TikTok API.
- Strict declared-country and metadata gates reduce recall; legitimate missing-country or multilingual channels may be excluded.
- Search is a single page per click and is not exhaustive. A narrow localized phrase can be sparse. Niche labels are title keyword evidence, not an independently established specialization.
- Mean lifetime views of videos published during a period differ from views earned during the period. Mixed video formats are not normalized; latest-50 sampling can be incomplete and is flagged.
- API fields can be missing, inaccurate or stale. Audience geography, honesty, rates, availability, contact ownership and partnership suitability still require human verification.
- No sponsor spreadsheet range was treated as measured 30/90-day performance or audience evidence.
