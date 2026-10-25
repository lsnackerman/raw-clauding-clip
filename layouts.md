# Layouts — where things sit in each show's frame

A vertical (9:16) clip is assembled from boxes cropped out of the source frame. Each preset below gives those boxes as `crop: [width, height, x, y]` in **source pixels**, plus where each lands on the 1080×1920 canvas. Pieces are placed in order, so later ones sit on top. `width` scales the piece; height follows. Omit `x` to center.

**Before trusting a preset, grab a frame and check it.** Shows change their look; a preset is a starting point, not a guarantee.

---

## BrewFOs (YouTube, 1920×1080, 24fps)

Two webcams side by side, BrewFOs logo above, the guest's name label below their panel. Guest on the left, Chad on the right.

**16:9:** the frame as-is, captions in the black bar at the bottom: `{"type": "full", "font": 58, "margin_v": 40, "outline": 3}`.

**9:16, panels stacked** (logo · guest · name label · Chad · captions):
```json
{"type": "canvas", "w": 1080, "h": 1920, "font": 76, "margin_v": 70, "outline": 4,
 "pieces": [
   {"crop": [480, 80, 720, 180], "width": 720, "y": 90},
   {"crop": [956, 540, 0, 270], "width": 1080, "x": 0, "y": 240},
   {"crop": [400, 100, 15, 828], "width": 560, "x": 30, "y": 860},
   {"crop": [956, 540, 964, 270], "width": 1080, "x": 0, "y": 1010}
 ]}
```
*Checked on ep 29 (Clint Weldon) and ep 28 (Sarah Gamm, whose two-line label "SARAH GAMM / @sarahgracewarrior" fit as-is), 2026-10-17; and on ep 26 (Vince Hall, "VINCE HALL / @uap_pod", the same day), as-is. If a guest's name runs longer, widen the name-label crop. Chad's edits sometimes add graphics over the guest panel (ep 28 has Mulder and Scully cutouts at 29:13–29:18); they ride along in the crop.*

**Older episodes: the logo sits higher and wider.** On ep 21 (Timothy Hogan, checked 2026-10-18) the logo spans x 648–1277, y 134–220, so the preset's logo crop catches only its bottom half (frame 0 shows a cut-off "BrewFOs"). Use `{"crop": [654, 108, 636, 124], "width": 720, "y": 100}`; the panels and the name label (Tim's two-line red label) fit the preset as-is. Check the logo on frame 0 of every older episode, and add its era here once more are measured.

**Ep 23 (Iya Whiteley, checked 2026-10-21):** the panels meet at x 960 (the preset's 956/964 crops still fit); the logo spans x 737–1187, y 175–237, so use the logo crop `[480, 80, 720, 168]` (the preset's starts 5px into it).

**Chad's own text captions in the bottom bar** (a guest's name and title under a photo, a fact under the panels; ep 23 rows ~890–1003) sit exactly where the clip's captions go, and the whole-frame `cuts` scan misses them (text barely moves the score). Find them with `clip.py cuts SLICE 1200:130:360:890`. Captions keep one position per format, so give the **16:9 one canvas for the whole clip with the picture 120px higher** (no jump mid-clip; the clip's captions land under his text): `{"type": "canvas", "w": 1920, "h": 1080, "font": 58, "margin_v": 40, "outline": 3, "pieces": [{"crop": [1920, 960, 0, 120], "width": 1920, "x": 0, "y": 0}]}`. In the 9:16, split at his caption's frames and lay it as a strip over the bottom of Chad's panel (below his chin): `{"crop": [1340, 120, 290, 887], "width": 1080, "x": 0, "y": 1528}` added to the stacked preset.

**A photo with Chad's name caption, or two book covers, over the seam** (ep 23, Dean Radin's photo at x 688–1232 with *"Dean Radin, PhD / Parapsychologist…"* below it, then *Real Magic* and *The Science of Magic* at x 643–1360):
```json
{"pieces": [{"crop": [480, 80, 720, 168], "width": 720, "y": 90},
            {"crop": [688, 540, 0, 270], "width": 860, "x": 110, "y": 240},
            {"crop": [544, 544, 688, 268], "width": 640, "x": 220, "y": 925},
            {"crop": [1290, 80, 315, 901], "width": 1080, "x": 0, "y": 1572}]}
{"pieces": [{"crop": [480, 80, 720, 168], "width": 720, "y": 90},
            {"crop": [643, 540, 0, 270], "width": 760, "x": 160, "y": 240},
            {"crop": [717, 548, 643, 267], "width": 960, "x": 60, "y": 895}]}
```

**Ep 18 (Dan Cleary, checked 2026-10-21):** the logo is larger, x 712–1213, y 169–241: `{"crop": [520, 84, 703, 163], "width": 720, "y": 100}`. The guest label is four lines: the name sits INSIDE the bottom-left of his panel (so it rides along with the panel crop) and three handles sit below it (x 16–222, y 826–922): `{"crop": [230, 104, 8, 822], "width": 322, "x": 30, "y": 860}`.

**Ep 19 (Pavel Ibarra, checked 2026-10-21):** the same family as ep 18. The logo spans x 750–1174, y 176–237, so the ep 23 logo crop `[480, 80, 720, 168]` fits. The name sits inside the bottom-left of his panel and two handles sit below it (x 28–313, y 823–903): `{"crop": [300, 90, 20, 818], "width": 420, "x": 30, "y": 860}`.

**Ep 20 (Scott Wolter, checked 2026-10-22):** the ep 18/19 family. The logo spans x 662–1265, y 148–239: `{"crop": [616, 100, 655, 144], "width": 720, "y": 100}`. The name sits inside his panel; two handles below it (x 18–369, y 822–913): `{"crop": [370, 100, 8, 818], "width": 480, "x": 30, "y": 860}`. Chad's text caption in the bottom bar (the Emerald Tablet quote, x 400–1520, y 887–961) went into the vertical IN PLACE of the handles for its 5.5 s: `{"crop": [1130, 84, 395, 882], "width": 1080, "x": 0, "y": 890}`, readable between the panels; the 16:9 used the raised canvas above.

**A graphic across the seam** (Chad's edits drop maps and images centred between the two panels; ep 26's map of Iraq at 6:03.58 sits at x 694–1225, y 267–812). The stacked 9:16 would cut it in two, so split the segment at the frame the graphic appears (`"crossfade": 0`, the same file continuing) and give that piece its own layout: the logo, the guest full width (cropped left of the graphic), the graphic whole below. Ep 26's, as used:
```json
{"pieces": [
   {"crop": [480, 80, 720, 180], "width": 720, "y": 90},
   {"crop": [694, 540, 0, 270], "width": 1080, "x": 0, "y": 240},
   {"crop": [532, 546, 694, 267], "width": 600, "y": 1092}
 ]}
```
Find the graphic's frame by sampling one pixel area per frame (it is a hard cut in Chad's edits), and its box from a full-size frame.

**A full-screen close-up of the guest** (Chad's edits sometimes zoom in on the guest, no logo, no panels; ep 21 at 0:27:48.3–0:29:05.0, found 2026-10-20). The stacked 9:16 crops it into nonsense, so give those frames their own layout, split at the zoom's first frame and at the first frame after it (`"crossfade": 0`, the same file continuing). Find them by sampling the band above the logo, black in the two-panel layout and picture in the close-up: `ffmpeg -i SLICE -vf "crop=400:80:760:0,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=yavg.txt" -f null -`, then print the frames where YAVG jumps past ~30. Ep 21's close-up, as used (the face large, no logo, captions below):
```json
{"pieces": [{"crop": [900, 1080, 380, 0], "width": 1080, "x": 0, "y": 240}]}
```
⭐ **If the clip's first word starts a few frames before the zoom** (ep 21's *"I mean"* starts 0.12s before it), cover those frames with the guest's panel blown up to match, in BOTH formats, so frame 0 is already the close-up: 9:16 `{"crop": [450, 540, 190, 270], "width": 1080, "x": 0, "y": 240}`; 16:9 as a one-segment canvas override, `{"type": "canvas", "w": 1920, "h": 1080, "pieces": [{"crop": [956, 540, 0, 270], "width": 1920, "x": 0, "y": 0}]}` (a segment's `formats` can change its `type`). Chad's zoom is about 3% tighter than the panel, invisible over 3 frames.

**Full-screen b-roll** (Chad's edits cut away to photos, documents and tables; ep 21 at 1:34:16–1:34:55: a photo of the Talpiot Tomb with his red caption, an ossuary photo, then a table of ossuary inscriptions). ⭐ **Detect any non-panel frame by the LOGO, not the top band:** the table had a black band at the top and a top-band scan missed it entirely. Sample the logo box (on ep 21, `crop=630:90:648:132,signalstats`), take a two-panel frame's YAVG/SATAVG/UAVG/VAVG as the reference (from a stretch you KNOW is two-panel: a slice that opens on a close-up gives a wrong reference), and flag any frame more than ~6 off on any of them. Then split and give each insert its own 9:16 layout, cropped to what it is FOR so it reads on a phone. Ep 21's, as used:
```json
{"pieces": [{"crop": [1035, 920, 582, 0], "width": 1080, "x": 0, "y": 240},
            {"crop": [1560, 80, 180, 950], "width": 1080, "x": 0, "y": 1215}]}
```
(a photo: cropped in on its subject, Chad's red caption below it as its own strip so the place stays named; on a photo without a caption the strip shows only a thin dark band) and
```json
{"pieces": [{"crop": [405, 680, 1161, 150], "width": 760, "x": 160, "y": 240}]}
```
(a table: only the column that matters, here "Tomb-ossuary inscription", measured off a still until no neighbouring column's letters show at either edge). Check every frame around each switch (`select='between(n\,A\,B)',tile=…`): a one-frame mismatch puts the wrong crop on the wrong shot.

⭐⭐ **Find EVERY insert by its hard cuts, not by brightness (2026-10-20).** A logo check misses graphics dropped over the panel seam (the logo is untouched), and a white-background check misses a dark photo. What every insert shares is a hard cut. Run `clip.py cuts SLICE` (the whole frame) and `clip.py cuts SLICE 832:540:544:270` (the box where Chad drops graphics on BrewFOs), then look at a frame inside each interval. It prints the half-frame segment edge for each cut. The whole frame alone misses a seam graphic's exit, which barely moves the whole-frame score. On ep 21 this found a dark skull photo that the white check missed, and full-screen b-roll inside the 10-18 sea-of-consciousness clip that every earlier check had sampled around.

**Graphic over the seam, any width:** logo, the guest's side cropped at the graphic's left edge, the graphic whole below. Ep 21, two graphics in a row with different boxes (x 544–1376 and 596–1324):
```json
{"pieces": [{"crop": [654, 108, 636, 124], "width": 720, "y": 100},
            {"crop": [544, 540, 0, 270], "width": 760, "x": 160, "y": 240},
            {"crop": [832, 540, 544, 270], "width": 1000, "x": 40, "y": 1000}]}
```
**B-roll with Chad's red caption:** shown full width, the caption shrinks to ~18px and can't be read on a phone, and it's his context (a counterpoint, a name). Crop the picture ABOVE the caption, and the caption as its own strip at full width below it (~27–36px). Find the caption's box by its red pixels (R > 180, G and B < 70). Ep 21's triptych and the SKYWATCHER footage (letterboxed, subject on the right):
```json
{"pieces": [{"crop": [1920, 760, 0, 0], "width": 1080, "x": 0, "y": 520},
            {"crop": [1770, 180, 75, 758], "width": 1080, "x": 0, "y": 960}]}
{"pieces": [{"crop": [1080, 710, 840, 190], "width": 1080, "x": 0, "y": 400},
            {"crop": [1490, 76, 215, 930], "width": 1080, "x": 0, "y": 1130}]}
```
⚠️ **Put every layout edge on a HALF-frame**, `(n - 0.5) / 24` where `n` is the first frame of the new shot. An edge exactly on a frame time can round either way, and one render put a b-roll frame through the two-panel crop.

**From the original recording files** instead of YouTube: they're likely higher quality (and skip the download), but the layout may differ from the published edit. Grab a frame and re-measure, and add the preset here.

---

## Beyond With Sean (YouTube, 1280×720, 30fps)

A slide fills most of the frame; two small webcams stack at the left (Sean on top, guest below), each with a name label; BEYOND logo top right.

**16:9:** captions raised into the blank part of the slide, clear of its footer: `{"type": "full", "font": 40, "margin_v": 135}`.

**9:16, webcams stacked** (logo · Sean · guest · captions):
```json
{"type": "canvas", "w": 1080, "h": 1920, "font": 68, "margin_v": 60,
 "pieces": [
   {"crop": [130, 134, 1130, 16], "width": 220, "y": 40},
   {"crop": [230, 172, 6, 185], "width": 900, "y": 300},
   {"crop": [230, 174, 6, 360], "width": 900, "y": 990}
 ]}
```
*Checked on ep 2 (Clint Weldon guesting), 2026-10-17. The webcams are only 230px wide, so they're enlarged ~4× and look soft; that's the source's limit. A full-frame letterbox is the other option: sharper, but the people are tiny. Pick per clip.*

---

## Zoom recordings (local, 1920×1080)

Zoom recordings switch between speaker view, gallery view and screen share within one session, so a preset only holds for a stretch. See SKILL.md § Before it goes public: screen shares show browser chrome, and classes show people who haven't agreed to be in a clip.

**Screen share of Google Slides, 1920×1200** (a class taught over Zoom): slide in the middle, the active speaker's camera tile top right. Never use the full frame; the browser's tabs and bookmarks are in it. Crop the slide `[1320, 742, 402, 292]` and the tile `[320, 180, 1600, 0]`:
- **9:16:** tile on top (`width` 1080, `y` 150), slide below (`width` 1080, `y` 790), `font` 72, `margin_v` 180.
- **16:9** (a 1920×1080 canvas): slide filling it (`width` 1920), tile as picture-in-picture (`width` 420, `x` 1480, `y` 20), `font` 58, `margin_v` 60.

**The tile shows whoever spoke last**, so check frames across the whole window, not one: in one class recording the tile still showed a student until a second after the teacher started talking, and the slide flickered while she navigated. Some recordings are 1920×1080 with the browser at a different offset; re-measure.

---

## Measuring a new layout

1. `clip.py frame FILE SEC frame.jpg` and read it.
2. Crop a generous region around the box you want at 2× (e.g. `ffmpeg -ss SEC -i FILE -frames:v 1 -vf "crop=260:420:0:160,scale=520:-1" test.png`) and read that; edges are easy to see at 2×. Convert back: source = crop offset + (pixel ÷ 2).
3. Render once, read a frame from the output, adjust.
