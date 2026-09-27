# Discovery evidence and market accuracy update

Branch: `codex/discovery-evidence-market-accuracy`
Base: `94dfad9` (`main`)
Verified: 27 September 2026

The existing working prototype has been improved in place. This update focuses on discovering relevant creators and handing off a defensible CSV shortlist.

## Added

- A country/market selector in live discovery, including **Germany**, connected to existing localized terms and language options. Market is sent as a YouTube search hint and included in the server cache key.
- Creator country and country source, target search market, content language and independently verified audience country as **separate fields** in cards, details, comparison and export.
- A shared 30/90-day upload-view summary with included video IDs, sample size, window boundaries, last-checked timestamp, insufficient-sample status, missing-view flags and a latest-50 cap indicator.
- Recent-title-based niche, game and hardware labels, with example-video links. Examples include Counter-Strike/CS2, Fortnite, Minecraft, Valorant, GPUs, CPUs and memory.
- Conservative extraction of explicit public contact emails/links from contact-labelled channel-description lines, with provenance. Unavailable contact information reads **No public contact found**.
- English documentation, live verification records and regression tests covering country/language contradictions, averages, provenance, filtering and CSV completeness.

## Changed

- Discovery inspects up to **50 latest public uploads** rather than combining five uploads with older search hits for the view average. Video API requests are batched at 50 IDs.
- View averages use videos published within **30 days**, falling back to **90 days** when fewer than three measured videos exist. Fewer than three in the fallback produces **Unknown**, not an unreliable average.
- Strict live eligibility requires the selected channel country, at least three inspected recent uploads, at least two matching language-metadata videos, and no explicit language conflict. Both audio-language and metadata-language fields are preserved. Search scores cannot bypass this gate.
- Niche scoring/filtering uses uploads published within 90 days. An old search hit no longer rescues a channel whose current content lacks the selected niche.
- New workspaces start with numeric thresholds disabled (0); existing saved settings are preserved. Positive thresholds retain the previous greater-than semantics. Sponsor collaboration ranges are guidance rather than hard eligibility cutoffs.
- Cards, details, comparison and CSV consume the same measured view summary. A single CSV example or an old API snapshot without the new measurement displays an unknown average.
- Shortlist CSV adds country/source, language/evidence, followers, view windows/sample/check time, contributing video URLs/counts, niche/game evidence, contact/source and missing-data flags, while retaining review notes, scores and outreach status.

## Fixed

- Foreign-language or wrong-country channels can no longer survive discovery because of a high engagement/view score or a single matching language tag.
- Search-matched videos outside the upload sample can no longer distort the recent average.
- Imported audience-location assertions are separate from verified audience geography, which remains Unknown.
- The “All sizes” label now correctly describes evidence-fit ranking. Existing ranking does not silently favor small creators.
- Comparison text uses the correct division symbol and readable separators.

## Preserved

Live YouTube discovery, localized queries, size/metric filters, adjustable explainable scoring, comparison, shortlist/review storage, CSV import/export, on-demand comments, existing fictional demos and optional local outreach drafts. No TikTok API, transcription system or extra outreach/contract workflow was added. No messages were sent; no API key was committed.

## Validation

- **22 Python tests passed**, plus both JavaScript regression suites and syntax checks for all four JavaScript modules.
- Real API searches were performed for **Finland, Germany and Sweden**. Recent titles, descriptions, country metadata and language evidence were inspected. Finland/Gaming yielded Napalmi; Germany/Budget gaming yielded Papa Oki and HardwareDealz after current-niche filtering. Sweden/Gaming yielded Teknikhype.
- Independent calculations matched exported CSV values for Napalmi (48 videos / 30 days), Papa Oki (6 / 90 days) and HardwareDealz (22 / 30 days).
- Browser verification covered market/language switching, numeric filtering, creator details, comparison, saved shortlist/review notes surviving reload, and individual/full-shortlist export controls. No browser errors were recorded during this flow.
- See [VERIFICATION.md](VERIFICATION.md) for exact snapshots, URLs and limits.

## Limitations

Strict country and metadata requirements may exclude useful creators with missing metadata or multilingual content. There is no text-only inference or provisional-results bucket. Estonia and Hungary were not added; existing six markets were prioritized. Contact detection does not unlock hidden emails or infer ownership. Niche labels are keyword heuristics requiring manual review. API metadata checks do not verify spoken language or audience geography. View counts are lifetime counts of sampled recent publications; Shorts, completed streams and long videos are mixed, and high-volume channels may have a capped sample. The sponsor collaboration spreadsheet was not used as measured performance data.

## 60-second demo

1. **0–15 seconds:** choose Finland / Finnish / Gaming, all sizes; set both numeric limits to 0 if a saved workspace has older limits. Enter `pelikone`, then Search YouTube. Show the live-source label and strict exclusions.
2. **15–30 seconds:** open **Napalmi** if still returned. Show declared Finland, Finnish evidence, 1,940 subscribers and the measured 30-day view sample. Explain that this is a small creator below typical collaboration ranges, not automatically ineligible. Open the linked PC-build video.
3. **30–45 seconds:** point to niche/game evidence, public-contact status and **Unknown** audience geography. Save, mark Reviewing and note that audience suitability and business conflicts still need checking.
4. **45–60 seconds:** export the shortlist CSV and show country/source, language evidence, average/window/sample size, contributing video URLs and review notes. If time remains, switch to Germany / German / Budget gaming to show localized discovery and the 90-day fallback on Papa Oki.

Results and counts change over time. If a live query becomes sparse or the API fails, show that limitation and try another localized query or result page; never replace live results with fictional creators.
