// Launch video, three acts (decision of 2026-10-07):
// act 1, "Inégalités environnementales": map, the two neighbourhoods, bars
// filling theme by theme (heat, air and noise, housing);
// act 2, "Inégalités d'accès": the two walking lines racing to the nearest
// station and to the nearest accessible station, with counters;
// act 3, "Underlaid": final card.
// Real data only (src/data/pair.json). Texts in src/texts.ts.
// Rules: the first frame already shows the map, both pastilles and the
// title; every text at least 48 px except the sources line; nothing
// important in the bottom 10 % (y > 1215) nor within 64 px of the sides.
import '@fontsource/atkinson-hyperlegible/400.css'
import '@fontsource/atkinson-hyperlegible/700.css'
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from 'remotion'
import data from './data/pair.json'
import { TEXTS } from './texts'

export const FPS = 30
export const ACT2 = 330
export const ACT3 = 690
export const DURATION = 870 // 29 s
export const COVER_FRAME = 670 // still frame: "[x] min / [y] min"

const W = 1080
const SIDE = 64
const C = {
  text: '#101010', text2: '#3C3C3C', grey: '#6A6A6A', line: '#D6D6D6', soft: '#ECECEC',
  pink: '#E4007C', pinkBg: '#FCE4F0', free: '#00A06B', wheelchair: '#0057B8', blue: '#0057B8',
}
const FONT = '"Atkinson Hyperlegible", sans-serif'
const THEMES = ['thermal', 'pollution', 'housing'] as const
const clamp = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const
const ease = Easing.bezier(0.22, 1, 0.36, 1)
type Hood = typeof data.a
type Box = { x: number; y: number; w: number; h: number }

const rank10 = (r: number) => Math.min(9, Math.max(0, Math.round(r * 10)))
const focus = data.focus === data.a.code ? data.a : data.b
const other = focus === data.a ? data.b : data.a
const X = focus.station.free
const Y = focus.station.wheelchair

// Map boxes (map units) fitted to a screen rectangle.
function fit(pts: number[][], rect: { top: number; h: number }, pad: number): Box {
  const xs = pts.map((p) => p[0])
  const ys = pts.map((p) => p[1])
  let w = Math.max(...xs) - Math.min(...xs) + 2 * pad
  let h = Math.max(...ys) - Math.min(...ys) + 2 * pad
  const ratio = W / rect.h
  if (w / h < ratio) w = h * ratio
  else h = w / ratio
  const cx = (Math.max(...xs) + Math.min(...xs)) / 2
  const cy = (Math.max(...ys) + Math.min(...ys)) / 2
  return { x: cx - w / 2, y: cy - h / 2, w, h }
}
const MAP1 = { top: 425, h: 215 }
const MAP2 = { top: 350, h: 640 }
const MAP3 = { top: 560, h: 560 }
const box1 = fit([data.a.centre, data.b.centre], MAP1, 450)
const box2 = fit([...data.routes.free.points, ...data.routes.wheelchair.points], MAP2, 250)
const box3 = (() => {
  const [sw, sh] = data.size
  return fit([[0, 0], [sw, sh]], MAP3, 600)
})()

function lerpBox(a: Box, b: Box, t: number): Box {
  const w = a.w * Math.pow(b.w / a.w, t)
  const k = (w - a.w) / (b.w - a.w || 1)
  return { x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k, w, h: a.h + (b.h - a.h) * k }
}
function lerpRect(a: { top: number; h: number }, b: { top: number; h: number }, t: number) {
  return { top: a.top + (b.top - a.top) * t, h: a.h + (b.h - a.h) * t }
}

function Pastille({ x, y, s = 1, o = 1 }: { x: number; y: number; s?: number; o?: number }) {
  return (
    <div style={{ position: 'absolute', left: x - 20, top: y - 20, width: 40, height: 40, transform: `scale(${s})`, opacity: o }}>
      <div style={{ width: 40, height: 40, borderRadius: 20, background: '#fff', border: `6px solid ${C.text}`, boxSizing: 'border-box', display: 'grid', placeItems: 'center' }}>
        <div style={{ width: 12, height: 12, borderRadius: 6, background: C.text }} />
      </div>
    </div>
  )
}

// `tight`: smaller gaps between rows, for languages whose theme labels wrap
// on three lines (English); the French layout is unchanged.
function Bars({ frame, t, tight = false }: { frame: number; t: typeof TEXTS.fr; tight?: boolean }) {
  const gap = tight ? 12 : 22
  const appear = interpolate(frame, [ACT2, ACT2 + 20], [1, 0], clamp)
  const LABEL_W = 330
  const CELL_W = (W - 2 * SIDE - LABEL_W) / 2
  const cell = (hood: Hood, k: (typeof THEMES)[number], start: number) => {
    const e = hood.exposures[k]
    const fill = interpolate(frame, [start, start + 40], [0, e.rank], { ...clamp, easing: ease })
    return (
      <div style={{ width: CELL_W, paddingRight: 24, boxSizing: 'border-box' }}>
        <div style={{ fontSize: 48, fontWeight: 700, whiteSpace: 'nowrap', lineHeight: 1.1, opacity: interpolate(frame, [start + 25, start + 40], [0, 1], clamp) }}>
          {t.outOf10(rank10(e.rank))}
        </div>
        <div style={{ position: 'relative', height: 20, borderRadius: 10, background: C.soft, overflow: 'hidden', marginTop: 8 }}>
          <div style={{ position: 'absolute', left: '75%', top: 0, bottom: 0, right: 0, background: C.pinkBg }} />
          <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${fill * 100}%`, borderRadius: 10, background: e.quarter === 4 ? C.pink : C.text2 }} />
        </div>
      </div>
    )
  }
  return (
    <div style={{ position: 'absolute', left: SIDE, right: SIDE, top: 660, opacity: appear }}>
      <div style={{ fontSize: 48, color: C.text2, lineHeight: 1.15, opacity: interpolate(frame, [30, 45], [0, 1], clamp) }}>{t.barsLegend}</div>
      <div style={{ display: 'flex', marginTop: gap, marginLeft: LABEL_W }}>
        {[data.a, data.b].map((h) => (
          <div key={h.code} style={{ width: CELL_W, fontSize: 48, fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden' }}>{h.name}</div>
        ))}
      </div>
      {THEMES.map((k, i) => {
        const start = 60 + i * 60
        return (
          <div key={k} style={{ display: 'flex', alignItems: 'flex-end', marginTop: gap, opacity: interpolate(frame, [start - 10, start], [0, 1], clamp) }}>
            <div style={{ width: LABEL_W, fontSize: 48, fontWeight: 700, lineHeight: 1.05, paddingRight: 16, boxSizing: 'border-box' }}>{t.themes[k]}</div>
            {cell(data.a, k, start)}
            {cell(data.b, k, start)}
          </div>
        )
      })}
    </div>
  )
}

export const Launch = ({ lang = 'fr' }: { lang?: 'fr' | 'en' }) => {
  const t = TEXTS[lang]
  const frame = useCurrentFrame()

  // Map placement and view through the three acts.
  const z12 = interpolate(frame, [ACT2 + 10, ACT2 + 70], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) })
  const z23 = interpolate(frame, [ACT3, ACT3 + 70], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) })
  const rect = z23 > 0 ? lerpRect(MAP2, MAP3, z23) : lerpRect(MAP1, MAP2, z12)
  const vb = z23 > 0 ? lerpBox(box2, box3, z23) : lerpBox(box1, box2, z12)
  const toScreen = (p: number[]) => [((p[0] - vb.x) / vb.w) * W, rect.top + ((p[1] - vb.y) / vb.h) * rect.h]
  const pa = toScreen(data.a.centre)
  const pb = toScreen(data.b.centre)

  // Act 2: the race. One minute of travel = RACE / Y frames.
  const RACE_START = ACT2 + 80
  const RACE = 240
  const m = interpolate(frame, [RACE_START, RACE_START + RACE], [0, Y], clamp)
  const progFree = Math.min(1, m / Math.max(X, 0.5))
  const progWc = Math.min(1, m / Math.max(Y, 0.5))
  const routeLine = (pts: number[][], prog: number) => {
    const s = pts.map(toScreen)
    const seg = s.slice(1).map((p, i) => Math.hypot(p[0] - s[i][0], p[1] - s[i][1]))
    const total = seg.reduce((a, b) => a + b, 0)
    const d = 'M' + s.map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join('L')
    return { d, total, end: s[s.length - 1], dash: total * (1 - prog) }
  }
  const rFree = routeLine(data.routes.free.points, progFree)
  const rWc = routeLine(data.routes.wheelchair.points, progWc)
  const act2Show = interpolate(frame, [ACT2 + 70, ACT2 + 85], [0, 1], clamp) * interpolate(frame, [ACT3, ACT3 + 20], [1, 0], clamp)

  // Cards (one per act, shown at the start of the act).
  const card1 = interpolate(frame, [ACT2, ACT2 + 15], [1, 0], clamp)
  const card1Text = interpolate(frame, [6, 24], [0, 1], clamp) * card1
  const card2 = interpolate(frame, [ACT2 + 5, ACT2 + 20], [0, 1], clamp) * interpolate(frame, [ACT3, ACT3 + 15], [1, 0], clamp)
  const card3 = interpolate(frame, [ACT3 + 10, ACT3 + 25], [0, 1], clamp)
  const card3Text = interpolate(frame, [ACT3 + 25, ACT3 + 40], [0, 1], clamp)
  const card3Cta = interpolate(frame, [ACT3 + 45, ACT3 + 60], [0, 1], clamp)
  const otherPastille = interpolate(frame, [ACT2 + 10, ACT2 + 40], [1, 0], clamp)
  const labels1 = interpolate(frame, [ACT2, ACT2 + 15], [1, 0], clamp)

  const head = (title: string, text: string | null, o: number, oText = o) => (
    <div style={{ position: 'absolute', left: SIDE, right: SIDE, top: 60 }}>
      <div style={{ fontSize: 72, fontWeight: 700, lineHeight: 1.05, opacity: o }}>{title}</div>
      {text ? <div style={{ fontSize: 48, lineHeight: 1.2, color: C.text2, marginTop: 18, opacity: oText }}>{text}</div> : null}
    </div>
  )
  // Name beside its pastille: the left one to the left, the other to the right.
  const label = (p: number[], text: string, o: number, toLeft: boolean) => (
    <div style={{ position: 'absolute', top: p[1] - 32, opacity: o, whiteSpace: 'nowrap', ...(toLeft ? { right: W - p[0] + 34 } : { left: p[0] + 34 }) }}>
      <span style={{ fontSize: 48, fontWeight: 700, background: 'rgba(255,255,255,0.9)', padding: '0 12px', borderRadius: 10 }}>{text}</span>
    </div>
  )

  return (
    <AbsoluteFill style={{ background: '#fff', fontFamily: FONT, color: C.text }}>
      <svg width={W} height={rect.h} viewBox={`${vb.x} ${vb.y} ${vb.w} ${vb.h}`} style={{ position: 'absolute', left: 0, top: rect.top }}>
        <path d={data.iris} fill="none" stroke={C.soft} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <path d={data.communes} fill="none" stroke="#C4C4C4" strokeWidth={1.4} vectorEffect="non-scaling-stroke" />
        <path d={data.paris} fill="none" stroke={C.grey} strokeWidth={2.2} vectorEffect="non-scaling-stroke" />
        <path d={data.a.path} fill={C.text} fillOpacity={0.08} stroke={C.text} strokeWidth={2.5} vectorEffect="non-scaling-stroke" opacity={focus === data.a ? 1 : otherPastille} />
        <path d={data.b.path} fill={C.text} fillOpacity={0.08} stroke={C.text} strokeWidth={2.5} vectorEffect="non-scaling-stroke" opacity={focus === data.b ? 1 : otherPastille} />
      </svg>

      {/* Act 2: the two lines. */}
      <svg width={W} height={1350} style={{ position: 'absolute', left: 0, top: 0, opacity: act2Show }}>
        <path d={rWc.d} fill="none" stroke={C.wheelchair} strokeWidth={9} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={rWc.total} strokeDashoffset={rWc.dash} />
        <path d={rFree.d} fill="none" stroke={C.free} strokeWidth={9} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={rFree.total} strokeDashoffset={rFree.dash} />
        <circle cx={rFree.end[0]} cy={rFree.end[1]} r={14} fill="#fff" stroke={C.free} strokeWidth={7} opacity={progFree >= 1 ? 1 : 0} />
        <circle cx={rWc.end[0]} cy={rWc.end[1]} r={14} fill="#fff" stroke={C.wheelchair} strokeWidth={7} opacity={progWc >= 1 ? 1 : 0} />
      </svg>

      <div style={{ position: 'absolute', left: Math.min(rFree.end[0] + 24, W - SIDE - 420), top: rFree.end[1] - 70, opacity: act2Show * (progFree >= 1 ? 1 : 0), fontSize: 48, fontWeight: 700, color: C.text, whiteSpace: 'nowrap' }}>
        <span style={{ background: 'rgba(255,255,255,0.9)', padding: '0 10px', borderRadius: 10 }}>{data.routes.free.stop}</span>
      </div>
      <div style={{ position: 'absolute', left: Math.min(rWc.end[0] + 30, W - SIDE - 420), top: rWc.end[1] + 18, opacity: act2Show * (progWc >= 1 ? 1 : 0), fontSize: 48, fontWeight: 700, color: C.wheelchair, whiteSpace: 'nowrap' }}>
        <span style={{ background: 'rgba(255,255,255,0.9)', padding: '0 10px', borderRadius: 10 }}>{data.routes.wheelchair.stop}</span>
      </div>
      <Pastille x={(focus === data.a ? pa : pb)[0]} y={(focus === data.a ? pa : pb)[1]} />
      <Pastille x={(focus === data.a ? pb : pa)[0]} y={(focus === data.a ? pb : pa)[1]} o={otherPastille * (1 - z23)} />
      {label(pa, data.a.name, labels1, pa[0] <= pb[0])}
      {label(pb, data.b.name, labels1, pb[0] < pa[0])}

      {/* Cards */}
      {head(t.act1Title, t.act1Text, card1, card1Text)}
      {head(t.act2Title, t.act2Text(X, Y), card2)}
      {head(t.act3Title, null, card3)}

      <Bars frame={frame} t={t} tight={lang === 'en'} />

      {/* Act 2: counters, in the order of arrival. */}
      <div style={{ position: 'absolute', left: SIDE, right: SIDE, top: 1010, opacity: act2Show }}>
        {[
          { color: C.free, n: Math.round(Math.min(m, X)), label: t.free, done: progFree >= 1 },
          { color: C.wheelchair, n: Math.round(m), label: t.wheelchair, done: progWc >= 1 },
        ].map((c, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'baseline', gap: 20, marginTop: i ? 14 : 0, opacity: i === 1 ? interpolate(frame, [RACE_START, RACE_START + 10], [0.4, 1], clamp) : 1 }}>
            <span style={{ width: 30, height: 30, borderRadius: 15, background: c.color, display: 'inline-block', transform: 'translateY(4px)' }} />
            <span style={{ fontSize: 80, fontWeight: 700, color: i === 1 ? C.wheelchair : C.text, minWidth: 250, fontVariantNumeric: 'tabular-nums' }}>{t.minutes(c.n)}</span>
            <span style={{ fontSize: 48, color: C.text2 }}>{c.label}</span>
          </div>
        ))}
      </div>

      {/* Act 3 */}
      <div style={{ position: 'absolute', left: SIDE, right: SIDE, top: 210 }}>
        <div style={{ fontSize: 52, lineHeight: 1.25, color: C.text2, opacity: card3Text }}>{t.act3Text}</div>
        <div style={{ fontSize: 60, fontWeight: 700, color: C.blue, marginTop: 30, opacity: card3Cta }}>{t.act3Cta}</div>
      </div>

      <div style={{ position: 'absolute', left: SIDE, right: SIDE, bottom: 30, fontSize: 18, color: C.grey, lineHeight: 1.35 }}>{t.sources}</div>
    </AbsoluteFill>
  )
}
