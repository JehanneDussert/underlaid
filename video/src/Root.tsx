import { Composition } from 'remotion'
import { DURATION, FPS, Launch } from './Launch'

// LinkedIn 4:5, 1080 x 1350, 30 fps, 29 s, no sound. One composition per
// language; every text is in src/texts.ts. Cover image: frame COVER_FRAME
// of the same composition (see package.json, "cover").
export const Root = () => (
  <>
    <Composition id="LaunchFR" component={Launch} durationInFrames={DURATION} fps={FPS} width={1080} height={1350} defaultProps={{ lang: 'fr' as const }} />
    <Composition id="LaunchEN" component={Launch} durationInFrames={DURATION} fps={FPS} width={1080} height={1350} defaultProps={{ lang: 'en' as const }} />
  </>
)
