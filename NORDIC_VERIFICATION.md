# Nordic / Baltic search verification — 27 September 2026

Branch: `codex/nordic-baltic-discovery-200`; base: `9b7e885`.

Live YouTube API searches used the configured server-side key, without logging or exporting credentials. The running app is served on `http://127.0.0.1:4173/`. Results below are a snapshot, not a guarantee of future counts.

## Configuration

- Recent-video discovery, relevance-first retrieval, Gaming niche.
- 800 minimum subscribers, no subscriber maximum, average-view filter disabled.
- Up to 200 unique channel IDs per market, 50 matches requested per page, maximum 12 search-page requests.
- Each native query alternative is searched independently; IDs are merged before country/language enrichment.
- Final displayed counts use the actual `filtered()` frontend function after backend filtering.

| Market | UTC retrieval time | Raw matches | Unique channels | Pass subscribers | Pass country | Pass language / views | Pass current niche / displayed | Search requests |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Finland | 11:56:01 | 550 | 200 | 167 | 55 | 46 | 39 | 11 |
| Sweden | 11:56:31 | 461 | 200 | 177 | 24 | 17 | 12 | 9 |
| Estonia | 11:56:46 | 407 | 200 | 137 | 13 | 9 | 6 | 9 |

All three stopped because the 200-unique-channel target was reached. No API warnings occurred. Repeated videos/channels explain why raw matches exceed 200. Country exclusions remain common; increased coverage does not turn region hints into a location guarantee. The 29 search-page requests used this run are within the existing 40-search local budget.

## Queries and examples

- Finland: `pelikone | pelitietokone | CS2 suomeksi | Fortnite suomeksi | Minecraft suomeksi`. Examples include [Napalmi](https://www.youtube.com/channel/UC3MbBJ8gywAevQF4PgfeTWg), [OssiTek](https://www.youtube.com/channel/UCG8arysCoaU6iFnSB3dVsIQ), [io-tech](https://www.youtube.com/channel/UCWVmpLlFWYD-ZMNdbw2hJzw) and [Aatso](https://www.youtube.com/channel/UC6rDl2h0s-SCZ9QELWMtFwg).
- Sweden: `speldator | datorspel | CS2 svenska | Fortnite svenska | Minecraft svenska`. Examples include [Teknikhype](https://www.youtube.com/channel/UCdbJCKT87le87K3EvICmWXA), [AffeDoom](https://www.youtube.com/channel/UCqa96Remwqn-sr28dyqkhDw) and [Grodan Gamer](https://www.youtube.com/channel/UCZ37YDUDMqTuj-OSiqeVg1w).
- Estonia: `mänguarvuti | arvutimängud | CS2 eesti keeles | Fortnite eesti | Minecraft eesti`. Displayed channels: [krispoiss](https://www.youtube.com/channel/UCsNcyPY9SB63nRunYpQPuPA), [krispoiss mängib](https://www.youtube.com/channel/UCaxv-A-Ip9adD_Hr-BzQf5A), [EstMagicz](https://www.youtube.com/channel/UC65Eq6kioOHsxDKah7disfQ), [Pait Gaming](https://www.youtube.com/channel/UCD1WO86syeV5FAYhB0XxLHg), [Reigo Tiivits](https://www.youtube.com/channel/UC2Et0VWyVBcu2LSZeQj4KQg) and [Level1](https://www.youtube.com/channel/UCk9hHu0uBBS9E-kgJBeIB2A).

These are discovery candidates, not approved partnerships. Gaming is intentionally broader than PC buying intent; mixed-content and business channels still require review. Country is channel-declared; language is API metadata; audience geography is unknown. Different niches, subscriber caps or positive view thresholds will produce smaller lists.

## Automated checks

28 Python tests and both JavaScript suites pass. Coverage includes reaching 200 unique IDs despite duplicates, 50-ID detail batches, round-robin query rotation, pagination termination, the 12-page request budget, partial-search warnings, Estonia support, local audio with English title metadata, contradictory audio, game-keyword eligibility, metric filters, median/ratio calculations and CSV exports.

The existing mean/median publication-window measurement remains unchanged. Live sample example: Napalmi mean 1,688.9375 / median 666; Teknikhype mean 4,901.2727 / median 3,116; Level1 mean 1,029.75 / median 1,026.5. These are lifetime views of sampled recent uploads, not channel views gained during the window.

## Browser and export checks

The locally served interface displayed 39 Finnish, 12 Swedish and 6 Estonian candidates using cached versions of these live API searches. Switching to Sweden/Estonia selected Swedish/Estonian and the appropriate query family. Creator cards displayed the median and ratio; krispoiss detail also showed median 20,088. The application was left running with the Estonian results open.

Exported 39 / 12 / 6 unreviewed discovery candidates using the application's real CSV export function. Python's CSV parser verified row counts and column alignment; an independent `statistics.median` calculation matched every available exported median from the included video IDs.
