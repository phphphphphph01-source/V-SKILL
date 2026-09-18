# V-SKILL Mobile + Buddy Item Layout Fix

Updated Buddy Studio responsive layout and Skill Item cards.

## Changes
- Skill Item preview is now isolated in a fixed-height viewport.
- Item artwork is constrained with `max-width` / `max-height` and cannot overlap the title, description, perk, or button.
- Item cards use a stable flex layout so buttons/unlock states stay at the bottom.
- Buddy cards use a stable preview/body layout.
- Added responsive layouts for tablet and mobile widths.
- Competition lobby/leaderboard collapse to one column on smaller screens.
- Bumped Buddy Studio CSS cache version to `20260917d`.

No database schema changes were made by this UI-only patch.
