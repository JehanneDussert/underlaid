// Pre-registered hypotheses and their verdicts, as published on the method
// page (part "Hypothèses et résultats"). Each hypothesis was written and
// dated before its crossing with residents' means was computed; the
// verdicts are applied exactly as the rules fixed in advance say
// (CLAUDE.md, "Hypothèse de travail", and SCORING.md). The figures of the
// third one are frozen results of scripts/analysis/routes_means.py (run of
// 3 October 2026, output data/interim/analysis/routes_means.txt): a
// pre-registered test is not recomputed each quarter.
//
// `control2022`: the same test redone with the 2022 census (rule of
// 3 October 2026, fixed before the results: the 2021 verdicts remain the
// official results; each gets a line "confirmed / not confirmed" with the
// figures). Outputs: data/interim/analysis/access_step4_rp2022.txt and
// routes_means_rp2022.txt.

export const HYPOTHESES = [
  {
    id: 'care',
    verdict: 'supported',
    written: '2026-10-01',
    // Share in the worst quarter for access to care, lowest / highest third.
    control2022: { confirmed: true, figures: { d92: [39.3, 24.0], d94: [38.8, 27.9], mgpGap: 22.9 } },
  },
  {
    id: 'wheelchair',
    verdict: 'refuted',
    written: '2026-10-01',
    control2022: { confirmed: true, figures: { d75: [52.3, 66.2], mgp: [13.2, 35.0] } },
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
    control2022: {
      confirmed: true,
      table: [
        { dep: '75', lowest: 1.7, highest: 6.2 },
        { dep: '92', lowest: 26.7, highest: 48.2 },
        { dep: '93', lowest: 22.2, highest: 49.7 },
        { dep: '94', lowest: 25.1, highest: 45.3 },
      ],
    },
  },
]
