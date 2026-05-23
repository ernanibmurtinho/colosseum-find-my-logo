---
name: logo-finder
description: Find a logo or icon inside a large mosaic/collage of icons, then crop+upscale it or render a CSI-style zoom-in animation landing on it. Use when someone wants to locate their logo in a hackathon mosaic (e.g. the Colosseum participant collage), find "where is X in this image", or make a zoom-reveal gif/video of a logo in a crowd of icons.
---

# Logo Finder

Find a logo in a sea of icons, then crop/upscale it or render a CSI-style zoom animation that flies from the full mosaic straight to the logo. OpenCV multi-scale template matching — no ML model, no GPU, no API keys.

## When to use

- "Find my logo in this mosaic / collage"
- "Where is `<project>` in the Colosseum mosaic?"
- "Make a zoom-in animation that lands on my logo"
- "Crop and upscale my icon out of this big image"

## Prerequisites

The `logo-finder` CLI must be on PATH. Check:

```bash
logo-finder --help
```

If it's missing, install it (this also installs this skill):

```bash
curl -fsSL https://raw.githubusercontent.com/ernanibmurtinho/colosseum-find-my-logo/main/install.sh | bash
```

GIF export is best with `ffmpeg` installed; MP4 works without it.

## Inputs

Two images from the user:

1. **logo** — a small, clean PNG of the logo to find (the template).
2. **mosaic** — the big collage/grid image to search (the haystack).

If the user only gives one, ask for the other. If their logo crop looks noisy or low-contrast, ask for a cleaner one — the template quality drives match quality.

## How to use

**1. Locate it:**

```bash
logo-finder find <logo.png> <mosaic.png>
```

Prints the match center coordinates + a confidence score in `[-1, 1]`. **> 0.9 is a strong match.** Add `-n 3` to see the top 3 candidates when you want to confirm the best one stands out.

**2. Crop + upscale:**

```bash
logo-finder enhance <logo.png> <mosaic.png> -o enhanced.png --size 1024
```

**3. Zoom animation (MP4 + GIF):**

```bash
logo-finder animate <logo.png> <mosaic.png> -o zoom.mp4 --gif zoom.gif
```

**One-shot (all three):**

```bash
scripts/find-my-logo.sh <logo.png> <mosaic.png> <out-prefix>
```

## Tips

- **A bad template is the #1 failure.** If `find` lands on the wrong icon, the fix is almost always a cleaner logo PNG, not different flags. Confidence < 0.8 → get a tighter, higher-contrast template.
- Matching is **color-aware** — hues disambiguate same-shaped icons (a white mark with a blue underline vs. a plain white shape).
- Icons not ~60–90 px in the mosaic? Widen the scale range: `--min-scale 40 --max-scale 130`.
- Rotated/skewed icons aren't supported (this is template matching, not feature matching).

## Output

Report the match **center + confidence** to the user first. Then point them at the enhanced crop and/or the zoom gif. If confidence is low, say so and suggest a cleaner template before they trust the result.
