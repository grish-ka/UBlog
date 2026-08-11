# Embedding this build in your existing site

## 1. Copy the build in

Copy the **contents of this folder** into your site at:

```
public/game/ea/instanceTest/
```

You should end up with `public/game/ea/instanceTest/index.html`, `public/game/ea/instanceTest/Build/`, and
`public/game/ea/instanceTest/TemplateData/`.

`vercel-headers-snippet.json` and this README are notes for you - they do no harm if
deployed, but you can delete them from `public/` if you prefer.

## 2. Merge the headers

Open `vercel-headers-snippet.json` and copy the objects from its `headers` array into the
`headers` array of **your site's existing** `vercel.json`. Do not replace the file - you
would lose whatever rules your chat site already relies on.

If your site has no `vercel.json` yet, create one containing just:

```json
{
  "headers": [ ...the objects from the snippet... ]
}
```

**Why this is required:** Unity ships pre-compressed `.br` files. Without
`Content-Encoding: br` the browser hands raw Brotli bytes to the WebAssembly parser and you
get a blank canvas with `Unable to parse Build/...`. The paths in the snippet already
include your `/game/ea/instanceTest` sub-path.

## 3. Add it to a page

### Option A - iframe (recommended)

Simplest, and it isolates the game's canvas and input handling from your chat UI.

```jsx
export default function GamePage() {
  return (
    <iframe
      src="/game/ea/instanceTest/index.html"
      title="Insances"
      allow="microphone; fullscreen; autoplay"
      style={{ width: '100%', height: '80vh', border: 0, display: 'block' }}
    />
  );
}
```

`allow="microphone"` is there for voice chat later. It must be present on the iframe from
the start - a nested document cannot request mic access without it, and adding it after the
fact is easy to forget when voice mysteriously fails.

### Option B - direct embed

Only worth it if the page needs to talk to the game (passing a username from your chat
system, for example).

```jsx
import { useEffect, useRef } from 'react';

export default function Game() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const script = document.createElement('script');
    script.src = '/game/ea/instanceTest/Build/{BUILD_NAME}.loader.js';
    script.onload = () => {
      createUnityInstance(canvasRef.current, {
        dataUrl: '/game/ea/instanceTest/Build/{BUILD_NAME}.data.br',
        frameworkUrl: '/game/ea/instanceTest/Build/{BUILD_NAME}.framework.js.br',
        codeUrl: '/game/ea/instanceTest/Build/{BUILD_NAME}.wasm.br',
        streamingAssetsUrl: '/game/ea/instanceTest/StreamingAssets',
      });
    };
    document.body.appendChild(script);
    return () => script.remove();
  }, []);

  return <canvas ref={canvasRef} style={{ width: '100%', height: '80vh' }} />;
}
```

Replace `{BUILD_NAME}` with the actual filenames in `Build/` - Unity names them after the
build output folder.

## 4. Deploy

Commit and push as usual. Vercel serves the whole thing from your existing domain.

## Notes

- Keyboard input only reaches the game while the canvas has focus. With an iframe, the
  player has to click the game once before WASD works - worth a hint on the page.
- Your chat site and the in-game chat are separate systems. In-game chat only reaches
  players inside the same hangar instance.
