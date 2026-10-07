# Launch video — "Deux adresses, quelques rues d'écart"

Remotion project (React). Real data only: `src/data/clichy.json` is written by
`scripts/prepare_data.py` from the files published on underlaid.fr
(neighbourhood files and map outlines) and from
`scripts/analysis/pair_walk_route.py` (walking time between the inhabited
centres of the two neighbourhoods, R5 on OpenStreetMap at 4.5 km/h).

Pair chosen on 7 October 2026: Clichy, Maison du Peuple / Bateliers
(search rule: `docs/checks/2026-10-06-neighbouring-pairs-rule.md`). Themes
shown: heat, air and noise, energy-inefficient housing (the gap on access to
care is small).

```bash
cd video
npm install
npm run studio   # preview
npm run render   # out/deux-adresses-clichy.mp4, 1080 x 1350, 30 fps, 22 s
npx remotion render src/index.ts DeuxAdressesStation out/deux-adresses-clichy-stations.mp4 --codec h264 --crf 18   # 26.5 s, with the station scene
```
