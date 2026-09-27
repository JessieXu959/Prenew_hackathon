# Community discovery demo

1. Choose a market/language, Channels or Recent videos, and a PRENEW niche preset. Estonia/Estonian and Hungary/Hungarian are supported.
2. Keep the subscriber floor at 800 or higher; optionally set an inclusive cap. Highest recent average views remains the default sort.
3. Review Matching candidates. Switch to Needs review for missing language/country evidence. Explicit language conflicts remain excluded. The declared-country restriction can be disabled; it never verifies audience geography.
4. Open a creator and select Analyze community. The app samples up to three relevant recent videos, with up to 20 popular and 20 recent top-level comments each. It verifies video ownership and deduplicates comments. There is no automatic sampling during discovery.
5. Inspect linked examples and observed creator replies. Keyword-assisted purchase/hardware/ownership labels are suggestions, not verified intent or authenticity judgments. Reply samples may be incomplete. Discord links are marked activity unverified.
6. Compare relevance, assessed discussion share, evidence coverage and reach. Save review notes and export the shortlist, including community collection time and source links.

## Formulas and limitations

- Relevance: percentage of supplied recent videos matching the selected niche keywords.
- Public interaction rate: mean of `(likes + comments) / views * 100` across eligible videos with known counts; score is `min(100, round(rate * 20))`.
- Community discussion share: percentage of sampled audience comments matching purchase/hardware/ownership keyword rules. General/uncertain comments remain in the denominator. Labels can overlap.
- Observed creator reply share: percentage of sampled audience-comment threads containing a returned creator reply. This is not a complete reply census.
- Repeat participants: sampled authors observed across at least two sampled videos.
- Evidence coverage: known checks out of five (measured views, language, creator country, sufficient community sample, public contact). It is not a trust score.
- Missing/unrun community analysis remains Not assessed. Public metrics do not establish sales, genuine engagement or audience location. Comment samples are not representative surveys. No messages are sent.

Validation: Python unit tests and both JavaScript suites cover sampling/deduplication, reply attribution, missing data, language presets, review separation, thresholds and exports. Live API and browser interaction were not exercised for this update. Restart the existing WSL server and refresh the browser to load backend changes.
