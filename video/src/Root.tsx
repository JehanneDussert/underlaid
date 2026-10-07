import { Composition } from 'remotion'
import { DeuxAdresses, DURATION, DURATION_STATION, FPS } from './DeuxAdresses'

// LinkedIn 4:5, 30 fps, about 22 s, no sound (readable without it).
export const Root = () => (
  <>
    <Composition id="DeuxAdresses" component={DeuxAdresses} durationInFrames={DURATION} fps={FPS} width={1080} height={1350} defaultProps={{ withStation: false }} />
    <Composition id="DeuxAdressesStation" component={DeuxAdresses} durationInFrames={DURATION_STATION} fps={FPS} width={1080} height={1350} defaultProps={{ withStation: true }} />
  </>
)
