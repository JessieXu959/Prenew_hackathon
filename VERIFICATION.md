# Verification

Verified in the local browser on 2026-09-26:

- Campaign form saves the supplied buyer brief and opens 20 creator recommendations.
- Two creators can be compared with scores, evidence coverage, language, audience market, views, fees and unknown conflicts.
- YouTube filter returns 7 profiles; fee sort is selectable.
- Creator details show scoring evidence and sample-content links.
- Selecting a concept enables outreach generation.
- Approving a generated draft moves the creator to Ready to Contact.
- Manual Contacted status and approval survive page refresh.
- Editing an approved draft enables reapproval; reapproval succeeds.
- Manual Confirmed status is read back successfully.
- Mobile layout checked at 390 × 844; comparison scrolls within its panel. Viewport reset afterward.
- Optional read-only WebMCP tool returns the same campaign/pipeline; invalid input is rejected.
- Language filtering normalizes regional tags such as `zh-Hans`, `zh-HK` and `sv-SE`; explicit non-selected languages are hidden while unknown metadata remains eligible.
- Country, language, niche, goal and edited query changes invalidate stale live results; creator-size changes filter the current set immediately.
- Live Sweden/Swedish verification hid nine explicit metadata mismatches returned by YouTube instead of displaying them as Swedish candidates.

The browser retains the earlier fictional Budget Respawn pipeline record for demo continuity. No messages were sent. YouTube live retrieval was verified with a locally configured key that remains outside Git. Seller-specific concepts were not separately exercised end-to-end. CSV upload and paste import were verified with synthetic test data in an isolated browser origin.
