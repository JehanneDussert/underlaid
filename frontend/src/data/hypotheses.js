// Pre-registered hypotheses and their verdicts, as published on the method
// page (part "Hypothèses et résultats"). Each hypothesis was written and
// dated before its crossing with residents' means was computed; the
// verdicts are applied exactly as the rules fixed in advance say
// (CLAUDE.md, "Hypothèse de travail", and SCORING.md). The figures of the
// third one are frozen results of scripts/analysis/routes_means.py (run of
// 3 October 2026, output data/interim/analysis/routes_means.txt): a
// pre-registered test is not recomputed each quarter.

export const HYPOTHESES = [
  {
    id: 'care',
    verdict: 'supported',
    written: '2026-10-01',
  },
  {
    id: 'wheelchair',
    verdict: 'refuted',
    written: '2026-10-01',
  },
  {
    id: 'publicServices',
    verdict: 'reversed',
    written: '2026-10-02',
    // Share of neighbourhoods in the quarter farthest from public services
    // (mean rank of the times to the town hall, France Services, CAF, CPAM,
    // France Travail and post office; Tuesday 10:00, on foot and by public
    // transport, no constraint), lowest and highest third of residents'
    // means computed within each département.
    table: [
      { dep: '75', lowest: 1.7, highest: 3.8 },
      { dep: '92', lowest: 27.2, highest: 48.2 },
      { dep: '93', lowest: 25.4, highest: 45.5 },
      { dep: '94', lowest: 25.1, highest: 46.2 },
    ],
  },
]
