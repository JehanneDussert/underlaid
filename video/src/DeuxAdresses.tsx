// "Deux adresses, quelques rues d'écart" — launch video, real data only
// (src/data/clichy.json, written by scripts/prepare_data.py from the files
// published on underlaid.fr). Identity of the site (redesign D4): white
// page, near-black text, Atkinson Hyperlegible, alert pink #E4007C for the
// most affected quarter only.
import '@fontsource/atkinson-hyperlegible/400.css'
import '@fontsource/atkinson-hyperlegible/700.css'
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import data from './data/clichy.json'

export const FPS = 30
export const DURATION = 660

const W = 1080
const MAP_TOP = 250
const MAP_H = 440
const C = { text: '#101010', text2: '#3C3C3C', grey: '#6A6A6A', line: '#D6D6D6', soft: '#ECECEC', pink: '#E4007C', pinkBg: '#FCE4F0' }
const FONT = '"Atkinson Hyperlegible", sans-serif'
const THEMES = [
  { key: 'thermal', label: 'Chaleur' },
  { key: 'pollution', label: 'Air et bruit' },
  { key: 'housing', label: 'Logements énergivores' },
] as const
type Hood = typeof data.a

const clamp = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const
const ease = Easing.bezier(0.22, 1, 0.36, 1)

// The phrase of the site, rounded the same way (rank x 10, between 0 and 9).
function sentence(rank: number) {
  const n = Math.min(9, Math.max(0, Math.round(rank * 10)))
  if (n === 0) return 'Sur 10 quartiers, aucun n’est moins exposé.'
  if (n === 1) return 'Sur 10 quartiers, 1 est moins exposé.'
  return `Sur 10 quartiers, ${n} sont moins exposés.`
}

const nf = (v: number) => new Intl.NumberFormat('fr-FR').format(v)

// Map view: from the two neighbourhoods (close-up) to the whole metropolis.
function viewBox(t: number) {
  const [cx, cy] = [(data.a.centre[0] + data.b.centre[0]) / 2, (data.a.centre[1] + data.b.centre[1]) / 2]
  const closeW = 2300
  const close = { x: cx - closeW / 2, y: cy - (closeW * MAP_H) / W / 2, w: closeW }
  const [sw, sh] = data.size
  const farW = Math.max(sw, (sh * W) / MAP_H) * 1.04
  const far = { x: sw / 2 - farW / 2, y: sh / 2 - (farW * MAP_H) / W / 2, w: farW }
  // Interpolate the width geometrically, so the zoom feels even.
  const w = close.w * Math.pow(far.w / close.w, t)
  const k = (w - close.w) / (far.w - close.w || 1)
  return { x: close.x + (far.x - close.x) * k, y: close.y + (far.y - close.y) * k, w, h: (w * MAP_H) / W }
}

const toScreen = (p: number[], vb: ReturnType<typeof viewBox>) => [((p[0] - vb.x) / vb.w) * W, MAP_TOP + ((p[1] - vb.y) / vb.h) * MAP_H]

function Pastille({ x, y, s }: { x: number; y: number; s: number }) {
  return (
    <div style={{ position: 'absolute', left: x - 17, top: y - 17, width: 34, height: 34, transform: `scale(${s})` }}>
      <div style={{ width: 34, height: 34, borderRadius: 17, background: '#fff', border: `5px solid ${C.text}`, boxSizing: 'border-box', display: 'grid', placeItems: 'center' }}>
        <div style={{ width: 10, height: 10, borderRadius: 5, background: C.text }} />
      </div>
    </div>
  )
}

function Label({ x, y, text, side, o }: { x: number; y: number; text: string; side: 'left' | 'right'; o: number }) {
  const style = side === 'left' ? { right: W - x + 28 } : { left: x + 28 }
  return (
    <div style={{ position: 'absolute', top: y - 20, ...style, opacity: o, fontSize: 26, fontWeight: 700, background: '#fff', padding: '2px 10px', borderRadius: 8 }}>
      {text}
    </div>
  )
}

function Column({ hood, x, frame }: { hood: Hood; x: number; frame: number }) {
  const appear = interpolate(frame, [170, 200], [0, 1], clamp)
  return (
    <div style={{ position: 'absolute', left: x, top: 760, width: 470, opacity: appear }}>
      <div style={{ fontSize: 36, fontWeight: 700, color: C.text }}>{hood.name}</div>
      <div style={{ fontSize: 22, color: C.text2, marginTop: 2 }}>
        {hood.commune} · {nf(hood.population)} habitants
      </div>
      {THEMES.map((th, i) => {
        const start = 200 + i * 75
        const e = hood.exposures[th.key]
        const fill = interpolate(frame, [start, start + 40], [0, e.rank], { ...clamp, easing: ease })
        const text = interpolate(frame, [start + 25, start + 45], [0, 1], clamp)
        const worst = e.quarter === 4
        return (
          <div key={th.key} style={{ marginTop: i === 0 ? 22 : 16, opacity: interpolate(frame, [start - 15, start], [0.25, 1], clamp) }}>
            <div style={{ fontSize: 25, fontWeight: 700, color: C.text }}>{th.label}</div>
            <div style={{ position: 'relative', height: 14, borderRadius: 7, background: C.soft, marginTop: 8, overflow: 'hidden' }}>
              <div style={{ position: 'absolute', left: '75%', top: 0, bottom: 0, right: 0, background: C.pinkBg }} />
              <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${fill * 100}%`, borderRadius: 8, background: worst ? C.pink : C.text2 }} />
            </div>
            <div style={{ fontSize: 21, color: C.text2, marginTop: 6, opacity: text, minHeight: 54, lineHeight: 1.3 }}>
              {sentence(e.rank)}
              {worst ? <span style={{ color: C.text, fontWeight: 700 }}> Dans le quart le plus exposé.</span> : null}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export const DeuxAdresses = () => {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const zoom = interpolate(frame, [500, 590], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) })
  const vb = viewBox(zoom)
  const mapIn = interpolate(frame, [25, 70], [0, 1], clamp)
  const pa = toScreen(data.a.centre, vb)
  const pb = toScreen(data.b.centre, vb)
  const popA = spring({ frame: frame - 80, fps, config: { damping: 12 } })
  const popB = spring({ frame: frame - 95, fps, config: { damping: 12 } })
  const draw = interpolate(frame, [110, 160], [0, 1], { ...clamp, easing: ease })
  // Curved line between the two inhabited centres (not the route).
  const mx = (pa[0] + pb[0]) / 2
  const my = (pa[1] + pb[1]) / 2
  const dx = pb[0] - pa[0]
  const dy = pb[1] - pa[1]
  const len = Math.hypot(dx, dy) || 1
  const bend = Math.min(160, len * 0.35)
  const ctrl = [mx + (-dy / len) * bend, my + (dx / len) * bend]
  const curve = `M${pa[0]},${pa[1]} Q${ctrl[0]},${ctrl[1]} ${pb[0]},${pb[1]}`
  const curveLen = len * 1.25
  const columns = interpolate(frame, [480, 505], [1, 0], clamp)
  const lineFade = interpolate(frame, [500, 530], [1, 0], clamp)
  const outro = interpolate(frame, [585, 610], [0, 1], clamp)
  const titleIn = interpolate(frame, [0, 22], [0, 1], clamp)

  return (
    <AbsoluteFill style={{ background: '#fff', fontFamily: FONT, color: C.text }}>
      <div style={{ position: 'absolute', left: 60, top: 56, right: 60, opacity: titleIn, transform: `translateY(${(1 - titleIn) * 12}px)` }}>
        <div style={{ fontSize: 56, fontWeight: 700, lineHeight: 1.1 }}>Deux adresses, quelques rues d’écart.</div>
        <div style={{ fontSize: 28, color: C.text2, marginTop: 12 }}>
          Clichy (Hauts-de-Seine) · {data.walk_minutes} minutes à pied
        </div>
      </div>

      <svg width={W} height={MAP_H} viewBox={`${vb.x} ${vb.y} ${vb.w} ${vb.h}`} style={{ position: 'absolute', left: 0, top: MAP_TOP, opacity: mapIn }}>
        <path d={data.iris} fill="none" stroke={C.soft} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        <path d={data.communes} fill="none" stroke="#C4C4C4" strokeWidth={1.4} vectorEffect="non-scaling-stroke" />
        <path d={data.paris} fill="none" stroke={C.grey} strokeWidth={2.2} vectorEffect="non-scaling-stroke" />
        <path d={data.clichy_iris} fill="none" stroke={C.line} strokeWidth={1.4} vectorEffect="non-scaling-stroke" opacity={1 - zoom} />
        <path d={data.a.path} fill={C.text} fillOpacity={0.08} stroke={C.text} strokeWidth={2.5} vectorEffect="non-scaling-stroke" />
        <path d={data.b.path} fill={C.text} fillOpacity={0.08} stroke={C.text} strokeWidth={2.5} vectorEffect="non-scaling-stroke" />
      </svg>

      <svg width={W} height={1350} style={{ position: 'absolute', left: 0, top: 0, opacity: lineFade }}>
        <path d={curve} fill="none" stroke={C.text} strokeWidth={4} strokeLinecap="round" strokeDasharray={curveLen} strokeDashoffset={curveLen * (1 - draw)} />
      </svg>
      <div
        style={{
          position: 'absolute', left: ctrl[0] - 110, top: ctrl[1] - 24, width: 220, textAlign: 'center',
          fontSize: 24, fontWeight: 700, opacity: interpolate(frame, [150, 170], [0, 1], clamp) * lineFade,
        }}
      >
        <span style={{ background: '#fff', padding: '4px 10px', borderRadius: 999, border: `1px solid ${C.line}` }}>{data.walk_minutes} min à pied</span>
      </div>
      <div style={{ opacity: lineFade }}>
        <Pastille x={pa[0]} y={pa[1]} s={popA} />
        <Pastille x={pb[0]} y={pb[1]} s={popB} />
        <Label x={pa[0]} y={pa[1]} text={data.a.name} side={pa[0] < pb[0] ? 'left' : 'right'} o={interpolate(frame, [90, 110], [0, 1], clamp)} />
        <Label x={pb[0]} y={pb[1]} text={data.b.name} side={pa[0] < pb[0] ? 'right' : 'left'} o={interpolate(frame, [105, 125], [0, 1], clamp)} />
      </div>
      <div style={{ opacity: Math.max(0, zoom - 0.6) / 0.4 }}>
        <Pastille x={(pa[0] + pb[0]) / 2} y={(pa[1] + pb[1]) / 2} s={1} />
      </div>

      <div style={{ opacity: columns }}>
        <div style={{ position: 'absolute', left: 539, top: 760, width: 2, height: 400, background: C.line, opacity: interpolate(frame, [170, 200], [0, 1], clamp) }} />
        <div style={{ position: 'absolute', left: 40, right: 40, top: 712, fontSize: 21, color: C.grey, opacity: interpolate(frame, [170, 200], [0, 1], clamp) }}>
          Position parmi les 2 752 quartiers de Paris et de la petite couronne (le quart le plus exposé en rose)
        </div>
        <Column hood={data.a} x={40} frame={frame} />
        <Column hood={data.b} x={570} frame={frame} />
      </div>

      <div style={{ position: 'absolute', left: 60, right: 60, top: 790, textAlign: 'center', opacity: outro, transform: `translateY(${(1 - outro) * 12}px)` }}>
        <div style={{ fontSize: 76, fontWeight: 700 }}>Et le vôtre ?</div>
        <div style={{ fontSize: 46, fontWeight: 700, color: '#0057B8', marginTop: 18 }}>underlaid.fr</div>
        <div style={{ fontSize: 26, color: C.text2, marginTop: 22 }}>Les 2 752 quartiers de Paris et de la petite couronne</div>
      </div>

      <div style={{ position: 'absolute', left: 40, right: 40, bottom: 24, fontSize: 16, color: C.grey, lineHeight: 1.35 }}>
        Quartiers : découpage Insee, environ 2 000 habitants. Données : Insee, CSTB, L’Institut Paris Region, Airparif et Bruitparif, ADEME, Enedis. Trajet à pied entre les centres habités des deux quartiers : © les contributeurs d’OpenStreetMap. Méthode : underlaid.fr/methode
      </div>
    </AbsoluteFill>
  )
}
