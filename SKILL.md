---
name: clip
description: Cut a short captioned video clip (16:9 and/or vertical 9:16) from a YouTube video or a local recording — a testimonial, a quote, a moment worth sharing — with cuts placed between words and captions burned in.
argument-hint: [YouTube URL or video file] [the moment, roughly when]
---

# /clip — cut a moment worth sharing

You and the human you're working with pick a moment; this skill gets it out of a long video as a clean, captioned clip for LinkedIn, Instagram, a landing page, etc.

**It pulls clips from things already said. It adds nothing on top:** no B-roll, music, generated video or motion graphics. Only the person, their own words, and captions. Other short-video tools edit a fresh recording into a produced piece; this one finds and lifts what's already there.

**The split:** `clip.py` (in this folder) does what has a right answer: fetching the right formats, reading word timings, measuring loudness, rendering. **The judgment stays in the conversation**: which moment, where exactly it starts and ends, which layout, whether it lands. You can check timing and framing on stills; **you can't watch or hear the result, so the human's playback is the real check.**

---

## First time on a machine (setup)

`clip.py` needs three things. **Check first, then tell the human exactly what you'd install and get a yes before installing anything:**

| Need | Check | If missing |
|---|---|---|
| Python 3.10+ | `python3 --version` | python.org installer (macOS's built-in 3.9 is too old for yt-dlp) |
| yt-dlp (YouTube only) | `yt-dlp --version` | `uv tool install "yt-dlp[default]"` if you have uv, or `python3 -m pip install -U "yt-dlp[default]"` (pip refuses on Homebrew's Python; installed with Homebrew: `brew upgrade yt-dlp`). **A `403 Forbidden` on `fetch` while `vtt` works means it is too old:** update it |
| ffmpeg that can burn captions | `ffmpeg -hide_banner -filters \| grep subtitles` (a line back means yes; nothing back, or no ffmpeg, means no) | `python3 clip.py ffmpeg` fetches a static build through **uv** (~50 MB into uv's cache, nothing system-wide). **Ask first: that command is the download.** Homebrew's ffmpeg was built without the `subtitles` filter on the Mac we tested (8.1, 2026-10); `render` skips an ffmpeg like that and uses uv's. |
| uv (only if the ffmpeg check says no) | `uv --version` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` (from docs.astral.sh/uv; no Homebrew needed) |

No Homebrew required. Local recordings don't need yt-dlp at all. **Built and tested on macOS:** captions use its built-in fonts (`FONTS` near the top of `clip.py`). On Linux, point `FONTS` at a folder with Helvetica Neue or change the font in `ass()`. Windows is untested.

---

## The flow

Run commands from a scratch folder; `clip.py` is beside this file. `python3 clip.py` with no arguments prints its full help. **Put YouTube URLs in quotes:** macOS's shell (zsh) reads the `?` in `watch?v=` as a filename wildcard and refuses to run the command.

**1. Find the moment.** For YouTube, `clip.py vtt URL DIR` pulls the original-language auto-captions.
- **The human knows roughly where it is:** `clip.py words VTT START END` prints every word in that stretch with its start time.
- **Nobody knows where it is:** `clip.py transcript VTT` prints the whole video as timestamped 20-second paragraphs to read through (a 90-minute episode is ~14,000 words, unreadable as a word list). Auto-captions have no speaker names; `>>` only marks a change of speaker, so check a frame when it matters who's talking. Pick a moment that stands on its own, then show the human before cutting.
- **For a recording, use its transcript**, and take times from a file that timestamps every line. A cleaned-up transcript that only timestamps its section headings can be minutes off for anything inside a section.
- **Where people reacted is a good place to look:** someone saying "I'm writing that down," asking you to repeat a line, or quoting it back later. In a meeting recording, the chat log shows some of these.

**2. Get the footage.**
- **YouTube:** `clip.py fetch URL START END slice.mp4` downloads only that window (pad ~10s each side). It asks for H.264 and the **original-language** audio. Videos with YouTube's auto-dubs carry ~20 audio tracks, and grabbing one by number can hand you the speaker in Japanese. It prints the codec and where the slice starts. If the codec isn't `h264`, check `yt-dlp -F URL`. If the start isn't ~0, every slice time is off by that much (it warns).
- **A local recording:** no fetch. Point the spec at the file and use seconds from the file's start. A Zoom transcript (`.transcript.vtt`) has line timings, not word timings, so `words` won't help there; `levels` does the placing.
- **The same person can look different across recordings** (room light, a lamp set differently). When two tellings of a moment are equally good, ask the human which look they prefer. Never trade away the better moment for it.

**3. Look at a frame before choosing a layout.** `clip.py frame slice.mp4 SEC frame.jpg`, then read the image. Every show is laid out differently: side-by-side panels, a slide with small webcams, a screen share. Check `layouts.md` for a preset; for a new layout, crop a test image to find each box's pixel edges, and add the preset to `layouts.md` when it works. Look at a few frames across the moment, not one: a show's own edits (graphics, cutouts, a switch to a screen share) come and go mid-clip. If one would be cut apart by a layout (a map across the seam of a stacked vertical), split the segment at the frame it appears and give that piece its own layout (`clip.py`'s help; examples in `layouts.md`).
- **Then find every one with `clip.py cuts slice.mp4`**, and again with the box where the show drops graphics (`clip.py cuts slice.mp4 W:H:X:Y`), and once more on the band where it puts its own text captions (the whole-frame scan misses text). It prints each of the show's own cuts and the segment edge to use (half a frame before it). Sampled frames miss inserts: a clip once shipped with 8 seconds of b-roll sliced by the vertical's crop, and every frame anyone had looked at fell either side of it.
- **Someone else's camera tile showing?** In a meeting recording the tile shows whoever spoke last. Hold the frame with `video_start` (step 6), or give that stretch a layout without the tile: the slide alone, or a slide that fits what's being said.

**4. Place the cuts.** `clip.py levels slice.mp4 SEC DUR` prints loudness every 20ms. **Cut inside a dip between words** (about -40 dB or lower). Use the caption word times to know *which* dip, and the levels to know *where*: the captions have run ~0.1s early, on time and slightly late on different videos, so never apply a fixed offset. **Not every dip is a word boundary:** a dip can sit inside a long word.
- **The clip's very first cut goes in real silence** (−60 dB or lower), not a short dip: a short dip can sit inside a word, and the listener hears a clipped word with nothing before it to explain it. A transcriber won't catch it (it fills the fragment in); the human's ear will.
- **End where the speaker ends, not where a sentence ends.** A short pause after the last word often means they're still going. Read the next line: if it carries the same thought, keep going to their real stop.
- **A segment's `end` is where the sound stops**, so set it in the dip just after the last word, not on the word.
- **Splicing two moments?** Each cut needs to be in a dip too, but a short one is enough: the picture dissolves while the sound switches cleanly at the cut. `render` warns if a cut isn't quiet. Don't leave a joining word ("and," "so") at the end of the first piece; end it on a sentence.

**5. Write the captions** as `[start, end, "text"]` on the **output** timeline (seconds from the clip's first frame). **The first caption starts at 0.0:** frame 1 is the preview a feed shows before anyone hits play, so it should carry the picture *and* the opening words. For the first segment that's the word time minus the cut-in; a second segment starts at the first segment's length (`end − start`), a third at the first two added, and so on. The last caption can run into the held ending, up to the clip's last frame. **Build the caption times from the word list with a short script, not by hand**, and convert any source times to slice times the same way: hand arithmetic has put captions and cuts in plausible-looking wrong places. **Fix the transcriber's mistakes and spell names and brand terms the way their owners do.** Keep the speaker's words; fillers can stay or go, but don't rephrase. ~45 characters per line on 16:9; both formats wrap long lines themselves, and `\\N` in the JSON text forces a break.

**6. Render.** Write a spec (format in `clip.py`'s help; worked examples in `layouts.md`) and run `clip.py render spec.json`. Two options for awkward moments:
- **`"speed": 0.9`** plays it 10% slower with the pitch kept, for a fast talker. Captions and timings scale on their own. Past ~0.85 it starts to sound like playback; make it a variant to compare, not a default.
- **`"video_start"` on a segment** (later than its `start`) starts the sound at `start` and holds the picture's frame from `video_start` until then. Use it when the first word is spoken while a meeting tile still shows someone else. Put `video_start` a few frames past the switch, not on it: the switch frame itself can still show the other person.

It handles the joins and the ending: **the sound eases out over the last 40ms before the final `end`, then the last frame holds ~0.7s in silence while the picture and captions fade.** That's why `end` goes in the dip after the word: put it on the word and the fade eats it, which makes a clip "end a smidge short." A soft last word needs room: move `end` later, to just before the next voice, and raise `hold` (1.2s) so the ending doesn't feel rushed.

**7. Check, then hand it over.** Grab **frame 0** and one or two more from each output and read them (frame 0 shows the picture and the first caption, captions placed, nothing cropped wrong). `levels` on the last second confirms the word finishes before the silence. `render` also warns if the picture ends before the sound does; don't ship a clip that warns. Then send the clips to the human with what to listen for (a clipped first or last word).
- **Ask the human to check a vertical clip on a phone before it ships.** Phones can draw things computers don't (an iPhone showed a dashed strip on clips carrying Zoom's color tag; `render` now fixes that one, see `learnings.md`). If something shows up only on one device, test with one change per file and a known-clean control, and don't put a guessed fix into the tool until a test confirms it.
- **When a cut is a judgment call, send two or three versions instead of guessing.** Hearing them side by side is how the human finds the right one, sometimes the one you already had. Asked for a change, change only that.

---

## Before it goes public

- **Is anyone in it who didn't agree to be?** Interviews on a public show are public. **Class recordings, calls and meetings are not.** Crop to the person who agreed, or pick a moment where only they're on screen and audible.
- **What's in the frame besides the person?** Screen shares show browser tabs, inbox counts, email addresses, notifications. Crop to the content or use an on-camera moment.
- **Did you cut or reorder anything?** Dropping a stretch or splicing two moments out of order is fine for a highlight, but the dissolve (the spec's `crossfade`) should show it's an edit, not one continuous take. Say so when you hand it over.

---

## Where the clips go

Wherever your system keeps material for sharing. Name files so the person, the source and the gist read at a glance, with the format last: `video-{who}-{source}-{gist}-{16x9|9x16}.mp4`. Keep the spec beside the clips: it's the exact recipe if a caption needs fixing later, and re-rendering it on another machine gives a matching clip.

---

## Skill Check

1. **Did a cut land wrong, and what told you?** If levels or word times misled you, add the case to `learnings.md`.
2. **Did you have to measure a layout?** Add it to `layouts.md` so the next clip from that show starts with it.
3. **Anything you did by hand that `clip.py` should do?** Second time you do it by hand, it goes in the script.
