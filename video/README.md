# Launch video — "Deux adresses, quelques rues d'écart"

Remotion project (React). Real data only: `src/data/clichy.json` is written by
`scripts/prepare_data.py` from the files published on underlaid.fr
(neighbourhood files and map outlines) and from
`scripts/analysis/pair_walk_route.py` (walking time between the inhabited
centres of the two neighbourhoods, R5 on OpenStreetMap at 4.5 km/h).

Pair chosen on 7 October 2026: Picpus 8 / Picpus 16 (Paris 12e); act 2 from
Picpus 8 (Michel Bizot, 3 min on foot; Porte Dorée, the nearest accessible
stop, 14 min in a wheelchair). Data: `CODES=751124608,751124616
FOCUS=751124608` for `scripts/prepare_data.py` and `scripts/pair_routes.py`
(after `scripts/analysis/pair_stations.py`). Texts: `src/texts.ts` (French
validated; English draft to review). Themes shown: heat, air and noise,
energy-inefficient housing.

```bash
cd video
npm install
npm run studio   # preview
npm run render:fr   # out/underlaid-fr.mp4, 1080 x 1350, 30 fps, 29 s
npm run cover:fr    # out/underlaid-cover-fr.png (frame 670)
npx remotion render src/index.ts DeuxAdressesStation out/deux-adresses-clichy-stations.mp4 --codec h264 --crf 18   # 26.5 s, with the station scene
```
