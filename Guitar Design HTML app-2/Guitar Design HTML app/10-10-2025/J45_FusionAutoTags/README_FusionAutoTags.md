# Fusion Auto-Tag Snippets for J-45

These snippets auto-detect `COMPONENT` from names like **J45_TOP**, **J45_BACK**, etc., 
emit a SAFE_START header with material and policy info, and tag each operation with 
`STEPDOWN_MM` and `OP_CLASS` (ROUGH/FINISH).

## Files
- `AutoTags_Snippets.cps` — paste into your active Fusion post (.cps)
- `Example_Integration.cps` — shows where to call from `onOpen` and `onSection`

## Quick install
1. Open your existing `.cps` post in a text editor.
2. Paste the entire contents of **AutoTags_Snippets.cps** near the top (below license header).
3. In your post's `onOpen()` and `onSection()`, add:
   ```js
   AutoTags_onOpen();
   AutoTags_onSection(currentSection);
   ```
4. Ensure your **Setup name** or **Program name/comment** contains one of:
   - `J45_TOP`, `J45_BACK`, `J45_FRETBOARD`, `J45_BRIDGE`, `J45_NECK`
   (The first one found sets default `MATERIAL`, `STOCK_THICKNESS_MM`, and `POLICY_STEPDOWN_CAP_MM`.)

## Output tags (examples)
- Header:
  ```
  (=== SAFE_START ===)
  (COMPONENT=J45_TOP)
  (MATERIAL=SPRUCE)
  (STOCK_THICKNESS_MM=4.500)
  (POLICY_STEPDOWN_CAP_MM=2.000)
  (=== /SAFE_START ===)
  ```
- Per operation:
  ```
  (EXPECTED_TOOL=3)
  (TOOL_DIAMETER_MM=3.175)
  (STEPDOWN_MM=0.800)
  (OP_CLASS=FINISH)
  ```

## Notes
- Strategy classification is heuristic; adjust the `ROUGH_STRATEGIES`/`FINISH_STRATEGIES` lists to fit your ops.
- Stepdown detection tries several parameter names and falls back to `getMaximumStepDown()` when available.
- All values are emitted in **mm** for downstream tooling.
