# Tool Box Integration Patch (Wiring + Finish)

## CLI
- `python cli.py wiring:simulate assets/wiring_examples/strat_5way.json`
- `python cli.py wiring:export-steps assets/wiring_examples/strat_5way.json --out assets/wiring_examples/strat_5way.steps.json`
- `python cli.py finish:validate assets/finish_examples/les_paul_burst.schedule.json toolbox/finish/finish_schedule.schema.json`
- `python cli.py finish:report assets/finish_examples/les_paul_burst.schedule.json --out assets/finish_examples/les_paul_burst.txt`

## Vue
Place `apps/luthiers-tool-box/src/modules/*.vue` into your app; add routes to expose them.
