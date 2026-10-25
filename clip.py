#!/usr/bin/env python3
"""
clip.py — the mechanical half of /clip: fetch a slice, read word timings and
loudness so a human can place the cuts, and render captioned clips from a spec.

The judgment (which moment, where exactly to cut, which layout, does it land)
stays in the conversation. This script only does what has a right answer.

Subcommands
  ffmpeg                         print the ffmpeg path (fetches a static build via uv on first use)
  fetch URL START END OUT.mp4    download only START..END (H:MM:SS), H.264 video + ORIGINAL-language audio
  vtt URL OUTDIR                 download the original-language auto-caption VTT
  transcript VTT [SECONDS]       the whole video as timestamped paragraphs (default 20s each), to find a moment
  words VTT START END            print per-word timings from an auto-caption VTT (absolute H:MM:SS)
  levels FILE START DUR          print loudness in 20ms steps (dB) — cut at a dip, not a guess
  frame FILE SEC OUT.jpg         grab one frame (to look at the layout, or check a render)
  cuts FILE [W:H:X:Y]            every hard cut in the slice's own edit (or inside one box): where a layout must switch
  render SPEC.json              render every format the spec lists

Spec (JSON) — times inside a slice file are seconds from the slice's start:
  {
    "segments": [{"file": "slice.mp4", "start": 17.45, "end": 23.65}, ...],
    "crossfade": 0.3,               # picture dissolve between segments (only used with 2+)
    "audio_join": "cut",            # default: sound switches cleanly at the cut; "crossfade" overlaps it too
    "hold": 0.7,                    # silent held last frame after the last word
    "fps": 30,                      # optional: output frame rate (default: the source's)
    "speed": 0.9,                   # optional: play slower, pitch kept (default 1.0)
    "captions": [[0.15, 2.47, "text"], ...],   # times on the OUTPUT timeline
    "out": "/path/video-who-source-gist",      # suffix -{format}.mp4 is added
    "formats": {
      "16x9": {"type": "full", "font": 58, "margin_v": 40, "outline": 3},   # outline: optional caption outline px
      "9x16": {"type": "canvas", "w": 1080, "h": 1920, "font": 76, "margin_v": 70,
               "pieces": [{"crop": [w, h, x, y], "width": 1080, "x": 0, "y": 240}, ...]}
    }
  }
  "canvas" pieces are cropped from the source frame and placed in order, so later
  pieces sit on top. Per-show presets live in layouts.md beside this script.

  Per segment, optionally:
    "formats": {"9x16": {"pieces": [...]}}   # this segment's own layout (a show graphic, another recording;
                                             # it can change "type" too). "pieces": {"9x16": [...]} is the older,
                                             # pieces-only form and still works.
    "crossfade": 0                           # the dissolve INTO this segment; 0 = a hard cut
    "video_start": SEC                       # hold the picture on this frame until then (see render)
  A segment that starts exactly where the previous one ended in the same file joins
  seamlessly (no sound change), so splitting a stretch in two just to switch layout
  at the frame the show cuts to a graphic is invisible in every other format.

Lessons baked in (each cost a re-render; full story in learnings.md):
  - yt-dlp's default format can be ~290 kbps AV1; we ask for H.264 explicitly.
  - Videos with YouTube auto-dubs carry ~20 audio tracks; we ask for the one marked original.
  - xfade needs a declared frame rate: setpts -> fps -> settb, in that order.
  - Never fade audio over the last word: a ~40ms fade after it, then a silent held frame.
  - Never fade the picture in: frame 1 is the thumbnail a feed shows before play.
"""
import html, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FFBIN = Path.home() / ".cache" / "clip-skill" / "bin"
FONTS = "/System/Library/Fonts"


def die(msg):
    sys.exit(f"clip.py: {msg}")


def has_subtitles(ff):
    """Can this ffmpeg burn in captions? Homebrew's ffmpeg is built without libass, so it has
    no `subtitles` filter."""
    r = subprocess.run([ff, "-hide_banner", "-filters"], capture_output=True, text=True)
    return re.search(r"\bsubtitles\b", r.stdout) is not None


def ffmpeg_path(captions=False):
    """A system ffmpeg if there is one (and, for render, one that can burn captions);
    otherwise the imageio-ffmpeg static build via uvx, symlinked as FFBIN/ffmpeg so
    yt-dlp's --ffmpeg-location can use it."""
    sysff = shutil.which("ffmpeg")
    if sysff and (not captions or has_subtitles(sysff)):
        return sysff
    link = FFBIN / "ffmpeg"
    if link.exists():
        return str(link)
    if link.is_symlink():
        # The link points into uv's cache; `uv cache clean` leaves it dangling.
        link.unlink()
    if not shutil.which("uvx"):
        if sysff:
            die("this ffmpeg can't burn in captions (no `subtitles` filter: it was built without libass, as "
                "Homebrew's is) and there's no uv to fetch one that can. Install uv and retry: it puts a full "
                "static ffmpeg in uv's cache and nothing system-wide.")
        die("no ffmpeg and no uv. Install uv, or ffmpeg itself, and retry.")
    out = subprocess.run(
        ["uvx", "--from", "imageio-ffmpeg", "python", "-c",
         "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"],
        capture_output=True, text=True, cwd=str(Path.home()))
    exe = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else ""
    if not exe or not Path(exe).exists():
        die(f"couldn't get ffmpeg via uvx:\n{out.stderr[-800:]}")
    FFBIN.mkdir(parents=True, exist_ok=True)
    link.symlink_to(exe)
    return str(link)


def run(cmd, quiet=True):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        die(f"command failed ({cmd[0]}):\n{r.stderr[-1500:]}")
    return r.stdout + r.stderr


def info(ff, f):
    """`ffmpeg -i FILE` with no output prints the stream info and exits non-zero by design."""
    r = subprocess.run([ff, "-hide_banner", "-i", str(f)], capture_output=True, text=True)
    return r.stderr


def hms(s):
    """'1:15:38.7' or '75:38' or '4538.7' -> seconds"""
    parts = [float(p) for p in str(s).split(":")]
    sec = 0.0
    for p in parts:
        sec = sec * 60 + p
    return sec


# ---- fetch ---------------------------------------------------------------

# H.264 first (Instagram/LinkedIn-safe), <=1080p; audio = the ORIGINAL language track.
# The second and third alternatives keep working on videos with no dub tracks.
FORMAT = ("bv*[vcodec^=avc1][height<=1080]+ba[ext=m4a][format_note*=original]"
          "/bv*[vcodec^=avc1][height<=1080]+ba[ext=m4a]"
          "/b[ext=mp4]")


def cmd_fetch(url, start, end, out):
    ff = ffmpeg_path()
    out = Path(out)
    run(["yt-dlp", "--no-update", "--ffmpeg-location", str(Path(ff).parent),
         "--download-sections", f"*{start}-{end}", "-f", FORMAT,
         "--merge-output-format", "mp4", "-o", str(out.with_suffix("")) + ".%(ext)s", url])
    if not out.exists():
        die("download finished but the file isn't there")
    i = info(ff, out)
    v = re.search(r"Video: (\w+).*?, (\d+x\d+).*?(\d+(?:\.\d+)?) fps", i)
    a = re.search(r"Audio: (\w+)", i)
    st = re.search(r"start: ([\d.]+)", i)
    print(f"{out}  video={v.group(1) if v else '?'} {v.group(2) if v else ''} {v.group(3) if v else ''}fps  "
          f"audio={a.group(1) if a else '?'}  starts at {st.group(1) if st else '?'}s")
    if v and v.group(1) != "h264":
        print("  ⚠ not H.264 — check `yt-dlp -F URL` and pick an avc1 format")
    if st and float(st.group(1)) > 0.05:
        print("  ⚠ the slice doesn't start at 0, so slice times are off by that much; re-fetch or subtract it")


def cmd_vtt(url, outdir):
    os.makedirs(outdir, exist_ok=True)
    run(["yt-dlp", "--no-update", "--skip-download", "--write-auto-subs", "--write-subs",
         "--sub-langs", "en-orig,en", "--sub-format", "vtt",
         "-o", os.path.join(outdir, "%(id)s.%(ext)s"), url])
    for f in sorted(Path(outdir).glob("*.vtt")):
        print(f)
    print("(en-orig is the original-language track; on 2026-10-17 it downloaded when plain `en` hit HTTP 429)")


# ---- reading the material --------------------------------------------------

WORD = re.compile(r"<(\d+:\d+:\d+\.\d+)><c>\s*([^<]+?)</c>")


def clock(t):
    h, rem = divmod(t, 3600)
    m, sec = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{sec:06.3f}"


def parse_words(vtt):
    """[(seconds, word)] from an auto-caption VTT. Each word carries its start time,
    except the first word of a line, which starts at the cue's start."""
    text = Path(vtt).read_text(encoding="utf-8")
    out, seen, last_new = [], set(), None
    for block in text.split("\n\n"):
        lines = block.strip().splitlines()
        if len(lines) < 2 or "-->" not in lines[0]:
            continue
        # A rolling cue repeats the previous line above the new one; only the line
        # carrying <c> tags is new text.
        cue_start = hms(lines[0].split("-->")[0].strip())
        tagged = [l for l in lines[1:] if "<c>" in l]
        if tagged:
            body = html.unescape(tagged[-1])
            first = body.split("<", 1)[0].strip()
            words = [(cue_start, first)] if first else []
            words += [(hms(t), w.strip()) for t, w in WORD.findall(body)]
            last_new = re.sub(r"<[^>]+>", "", body).strip()
        else:
            # A short untagged line (one or two words) is new text with no word timing,
            # unless it just repeats the line before it (the 10ms "carry" cues do that).
            txt = html.unescape(lines[-1]).strip()
            if not txt or txt == last_new:
                continue
            words, last_new = [(cue_start, txt)], txt
        for t, w in words:
            if (t, w) not in seen:
                seen.add((t, w))
                out.append((t, w))
    return sorted(out)


def cmd_words(vtt, start, end):
    s, e = hms(start), hms(end)
    for t, w in parse_words(vtt):
        if s <= t <= e:
            print(f"{clock(t)}  {w}")
    print("(caption times are a guide to WHICH dip to cut in, not an offset: they've run "
          "~0.1s early, on time and slightly late on different videos. Place cuts with `levels`.)")


def cmd_transcript(vtt, every="20"):
    """The whole video as readable timestamped paragraphs, for finding a moment when
    nobody knows roughly where it is. `>>` marks a change of speaker."""
    every = float(every)
    paras, cur, cur_t = [], [], None
    for t, w in parse_words(vtt):
        if cur_t is None:
            cur_t = t
        if t - cur_t >= every and cur:
            paras.append((cur_t, " ".join(cur))); cur, cur_t = [], t
        cur.append(w)
    if cur:
        paras.append((cur_t, " ".join(cur)))
    for t, txt in paras:
        print(f"[{clock(t)[:-4]}] {txt}\n")
    print("(no speaker names in auto-captions; `>>` is only a turn change)")


def rms_series(ff, f, start, dur):
    """Loudness in dB per 20ms window over [start, start+dur]."""
    out = run([ff, "-hide_banner", "-ss", str(start), "-t", str(dur), "-i", f, "-vn", "-af",
               "aresample=44100,asetnsamples=882,astats=metadata=1:reset=1,ametadata=print",
               "-f", "null", "-"])
    # Overall.RMS_level when there are 2+ channels; channel 1 otherwise.
    vals = re.findall(r"Overall\.RMS_level=(\S+)", out) or re.findall(r"\.1\.RMS_level=(\S+)", out)
    return [-120.0 if v in ("-inf", "inf", "nan") else float(v) for v in vals]


def cmd_levels(f, start, dur):
    ff = ffmpeg_path()
    row = []
    for i, v in enumerate(rms_series(ff, f, start, dur)):
        db = "-inf" if v <= -119 else f"{v:.0f}"
        row.append(f"{float(start) + i * 0.02:.2f}:{db}")
        if len(row) == 8:
            print("  ".join(row)); row = []
    if row:
        print("  ".join(row))
    print("(dB per 20ms; a dip of ~-40 or lower between two words is a cut point. Not every dip is a word boundary.)")


def cmd_frame(f, sec, out):
    ff = ffmpeg_path()
    run([ff, "-loglevel", "error", "-y", "-ss", str(sec), "-i", f, "-frames:v", "1", out])
    print(out)


def cmd_cuts(f, box=None):
    """Every hard cut in a slice (or inside one box of it): where the show's own edit
    switches shot, so a layout can switch with it. A graphic dropped over part of the
    frame barely moves a whole-frame score, so pass the box where the show puts them.
    (Added 2026-10-20, after a vertical shipped with b-roll sliced by its crop.)"""
    ff = ffmpeg_path()
    _, _, fps = probe(ff, f)
    crop = f"crop={box.replace(',', ':')}," if box else ""
    tmp = Path(tempfile.mkdtemp()) / "cuts.txt"
    run([ff, "-loglevel", "error", "-i", f, "-vf",
         f"{crop}select='gt(scene\\,0.15)',metadata=print:file={tmp}", "-f", "null", "-"])
    times = [float(m) for m in re.findall(r"pts_time:([\d.]+)", tmp.read_text())] if tmp.exists() else []
    shutil.rmtree(tmp.parent, ignore_errors=True)
    for t in times:
        n = round(t * fps)
        print(f"{t:9.3f}  frame {n:6d}  edge {(n - 0.5) / fps:.4f}")
    print(f"({len(times)} cut(s){' in ' + box if box else ' in the whole frame'}. Look at a frame inside each "
          f"interval; give each shot its own layout, with segment edges at the 'edge' value, half a frame "
          f"before the cut, so rounding can only fall one way.)")


# ---- render ----------------------------------------------------------------

def ass(caps, w, h, font, margin_v, outline=None):
    outline = outline if outline is not None else max(2, round(font / 19))
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Helvetica Neue,{font},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,{outline},1,2,70,70,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def t(x):
        h_, r = divmod(x, 3600); m, s = divmod(r, 60)
        return f"{int(h_)}:{int(m):02d}:{s:05.2f}"
    return head + "".join(f"Dialogue: 0,{t(a)},{t(b)},Cap,,0,0,0,,{txt}\n" for a, b, txt in caps)


def probe(ff, f):
    m = re.search(r", (\d+)x(\d+)[ ,].*?(\d+(?:\.\d+)?) fps", info(ff, f))
    if not m:
        die(f"can't read size/fps from {f}")
    return int(m.group(1)), int(m.group(2)), float(m.group(3))


def layout_chain(src, fmt, fps, tag, speed=1.0):
    """Filter chain for one segment's video -> [v{tag}] in the target layout."""
    stretch = f"(PTS-STARTPTS)/{speed}" if speed != 1.0 else "PTS-STARTPTS"
    norm = f"setpts={stretch},fps={fps:g},settb=1/{round(fps)},format=yuv420p"
    if fmt["type"] == "full":
        return f"{src}{norm}[v{tag}]"
    W, H = fmt["w"], fmt["h"]
    pieces = fmt["pieces"]
    # Zero the source timestamps BEFORE compositing. Otherwise the black canvas
    # starts at t=0 and the pieces arrive a frame later, so frame 1 (the preview a
    # feed shows) is an empty canvas.
    parts = [f"color=black:s={W}x{H}:r={fps:g}[bg{tag}]",
             f"{src}setpts=PTS-STARTPTS,split={len(pieces)}" + "".join(f"[s{tag}_{i}]" for i in range(len(pieces)))]
    for i, p in enumerate(pieces):
        cw, ch, cx, cy = p["crop"]
        parts.append(f"[s{tag}_{i}]crop={cw}:{ch}:{cx}:{cy},scale={p['width']}:-2:flags=lanczos[p{tag}_{i}]")
    prev = f"[bg{tag}]"
    for i, p in enumerate(pieces):
        x = p.get("x", "(W-w)/2")
        nxt = f"[o{tag}_{i}]"
        parts.append(f"{prev}[p{tag}_{i}]overlay={x}:{p['y']}" + (":shortest=1" if i == 0 else "") + nxt)
        prev = nxt
    parts.append(f"{prev}{norm}[v{tag}]")
    return ";".join(parts)


def cmd_render(spec_path):
    spec_path = Path(spec_path).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    base = spec_path.parent
    ff = ffmpeg_path(captions=True)
    segs = spec["segments"]
    xf = spec.get("crossfade", 0.3) if len(segs) > 1 else 0
    hold = spec.get("hold", 0.7)
    files = [str((base / s["file"]).resolve()) for s in segs]
    _, _, fps = probe(ff, files[0])
    fps = float(spec.get("fps", fps))          # optional override; default = the source's rate
    # "speed": 0.9 plays the clip 10% slower, pitch kept, for a fast
    # talker. Segment times stay in SOURCE seconds and captions stay on the 1x output
    # timeline as usual; both are scaled here, so a spec reads the same at any speed.
    speed = float(spec.get("speed", 1.0))
    src_durs = [s["end"] - s["start"] for s in segs]
    durs = [d / speed for d in src_durs]       # output seconds from here on
    # The dissolve INTO each segment (a segment's own "crossfade" overrides the spec's;
    # 0 is a hard cut), and which joins continue the same footage without a gap.
    xin = [0] + [segs[i].get("crossfade", xf) for i in range(1, len(segs))]
    contig = [False] + [segs[i]["file"] == segs[i - 1]["file"] and abs(segs[i]["start"] - segs[i - 1]["end"]) < 0.001
                        for i in range(1, len(segs))]
    # How segments join. "cut" (default): the PICTURE dissolves but the SOUND switches
    # cleanly at the cut, because the next segment's video starts `xf` early as pre-roll.
    # Works even when the pause between words is a few hundredths of a second.
    # "crossfade": the old way, picture and sound both overlap by `xf`, which swallows
    # any syllable within it. Kept for clips approved that way.
    join = spec.get("audio_join", "cut")
    if join == "cut":
        end = sum(durs)                        # segment k starts at sum(durs[:k])
    else:
        end = sum(durs) - sum(xin)             # segment k starts at sum(durs[:k]) - sum(xin[1:k+1])
    total = end + hold
    out_base = Path(spec["out"])
    if not out_base.is_absolute():
        out_base = base / out_base             # relative to the spec, like segment files
    out_base.parent.mkdir(parents=True, exist_ok=True)

    # A crossfade overlaps the AUDIO too: the last `xf` seconds of one segment play
    # under the first `xf` of the next. If either side has speech there, the dissolve
    # eats a syllable (the "ends a smidge short" problem, arriving through the join).
    # Only the half of the window nearest the join matters: there each side is close
    # to silent, so a word there gets swallowed. A word ending at the far edge is barely
    # touched (an approved splice had one).
    for i in range(len(segs) - 1):
        if contig[i + 1]:
            continue                           # the same footage continues: nothing to hear at the join
        if join == "cut":
            # The sound switches right at the cut points, so each must sit in a dip.
            for label, f, t0 in ((f"end of segment {i + 1}", files[i], segs[i]["end"] - 0.02),
                                 (f"start of segment {i + 2}", files[i + 1], segs[i + 1]["start"] - 0.02)):
                loud = max(rms_series(ff, f, max(0, t0), 0.04), default=-99)
                if loud > -30:
                    print(f"⚠ the {label} isn't in a quiet spot ({loud:.0f} dB): the sound will jump there. "
                          f"Check `levels` and move the cut into a dip")
            continue
        half = xin[i + 1] / 2
        if not half:
            continue
        for label, f, st in ((f"end of segment {i + 1}", files[i], segs[i]["end"] - half),
                             (f"start of segment {i + 2}", files[i + 1], segs[i + 1]["start"])):
            loud = max(rms_series(ff, f, st, half), default=-99)
            if loud > -35:
                print(f"⚠ speech right at the join, {label} (peak {loud:.0f} dB in the {half:.2f}s next to it): "
                      f"the dissolve will soften it. Listen there; if it's swallowed, move the cut into a pause "
                      f"or shorten \"crossfade\"")
    # Captions go in a temp folder, not beside the spec: the path lands inside ffmpeg's
    # quoted subtitles='…' argument, and an apostrophe in a folder name ("Sam's Podcast")
    # closed the quote and killed the render (found by a cold read, 2026-10-24).
    tmp = Path(tempfile.mkdtemp(prefix="clip-captions-"))

    for name, fmt in spec["formats"].items():
        if fmt["type"] == "full":
            w, h, _ = probe(ff, files[0])
        else:
            w, h = fmt["w"], fmt["h"]
        cap_file = tmp / f"{name}.ass"
        caps = [[a / speed, b / speed, t] for a, b, t in spec["captions"]]
        cap_file.write_text(ass(caps, w, h, fmt["font"], fmt["margin_v"], fmt.get("outline")), encoding="utf-8")

        inputs, chains = [], []
        tempo = f",atempo={speed}" if speed != 1.0 else ""
        for i, (s, f) in enumerate(zip(segs, files)):
            pre = xin[i] * speed if join == "cut" else 0   # source seconds
            if s["start"] - pre < 0:
                die(f"segment {i + 1} starts {s['start']}s into its file; the dissolve needs {pre}s of "
                    f"footage before it. Fetch a slice with more lead-in")
            inputs += ["-ss", f"{s['start'] - pre:.3f}", "-t", f"{src_durs[i] + pre:.3f}", "-i", f]
            # A segment can carry its own layout ("formats": {"9x16": {...}}, for a show
            # graphic) or just its own crop boxes ("pieces": {"9x16": [...]}, for a recording
            # laid out differently from the others).
            seg_fmt = {**fmt, **s.get("formats", {}).get(name, {})}
            if name in s.get("pieces", {}):
                seg_fmt["pieces"] = s["pieces"][name]
            # "video_start" (later than "start"): the sound starts at "start" but the picture
            # holds its frame at "video_start" until then. For a first word that's spoken
            # while a meeting's camera tile still shows someone else (2026-10-19).
            lead = s.get("video_start", s["start"]) - s["start"]
            src = f"[{i}:v]"
            if lead > 0:
                # fps BEFORE tpad: tpad can only pad the start when it knows the frame rate,
                # and Zoom records variable-rate, so without it the hold silently never
                # happened and the picture ran 0.6s ahead of the sound (2026-10-19).
                chains.append(f"[{i}:v]trim=start={pre + lead:.3f},setpts=PTS-STARTPTS,fps={fps:g},"
                              f"tpad=start_mode=clone:start_duration={pre + lead:.3f}[vin{i}]")
                src = f"[vin{i}]"
            chains.append(layout_chain(src, seg_fmt, fps, i, speed))
            if join == "cut":
                last = i == len(segs) - 1
                # no fade where the same footage simply continues: the sound runs on unbroken
                fades = ("" if i == 0 or contig[i] else ",afade=in:st=0:d=0.012") + \
                        ("" if last or contig[i + 1] else f",afade=out:st={durs[i] - 0.012:.3f}:d=0.012")
                chains.append(f"[{i}:a]atrim=start={pre:.3f},asetpts=PTS-STARTPTS{tempo}{fades}[a{i}]")
            else:
                chains.append(f"[{i}:a]asetpts=PTS-STARTPTS{tempo}[a{i}]")
        # join segments
        v, a, t = "[v0]", "[a0]", durs[0]
        for i in range(1, len(segs)):
            off = t - xin[i]
            if xin[i]:
                chains.append(f"{v}[v{i}]xfade=transition=fade:duration={xin[i]}:offset={off:.3f}[vx{i}]")
            else:                              # a hard cut (concat resets the timebase; xfade needs it back)
                chains.append(f"{v}[v{i}]concat=n=2:v=1:a=0,settb=1/{round(fps)}[vx{i}]")
            if join == "cut":
                v, t = f"[vx{i}]", t + durs[i]
            else:
                chains.append(f"{a}[a{i}]" + (f"acrossfade=d={xin[i]}" if xin[i] else "concat=n=2:v=0:a=1") + f"[ax{i}]")
                v, a, t = f"[vx{i}]", f"[ax{i}]", off + durs[i]
        if join == "cut" and len(segs) > 1:
            chains.append("".join(f"[a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1[acat]")
            a = "[acat]"
        sub = str(cap_file).replace(":", r"\:")
        # No video fade-in: the first frame is the preview platforms show before
        # anyone hits play, so it has to be the picture, not black (2026-10-17).
        # Captions burn in BEFORE the fade-out, so they dim with the picture.
        # Output exactly the canvas size (1080x1920 for vertical, the platforms' own spec).
        # Do NOT pad it up to a multiple of 16: 1152x2048 was tried 2026-10-17 to dodge an
        # iPhone-only dashed strip, and a one-change-at-a-time test proved it CAUSED the strip.
        resize = ""
        chains.append(f"{v}tpad=stop_mode=clone:stop_duration={hold},"
                      f"subtitles='{sub}':fontsdir={FONTS},"
                      f"fade=out:st={end + 0.15:.3f}:d={max(0.2, hold - 0.15):.2f}{resize},"
                      # Always write standard HD color. Zoom stamps its files with the old SD
                      # matrix (bt470bg) and it rode through to the clips; an iPhone showed a
                      # dashed strip on those and not on BrewFOs clips tagged bt709 (2026-10-17).
                      f"scale=out_color_matrix=bt709:out_range=tv,"
                      # ...and tag the frames themselves: the vertical's black canvas carries no
                      # tags, so primaries and transfer came out "unknown" without this (2026-10-18).
                      f"setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709[vout]")
        chains.append(f"{a}afade=in:st=0:d=0.06,afade=out:st={end - 0.04:.3f}:d=0.04,apad=whole_dur={total:.3f}[aout]")
        out = f"{out_base}-{name}.mp4"
        run([ff, "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(chains),
             "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-crf", "18", "-preset", "slow",
             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
        d = re.search(r"Duration: (\S+),", info(ff, out))
        print(f"{out}  ({d.group(1) if d else '?'})")
        # The picture must run as long as the sound. A filter that silently drops or
        # fails to add frames leaves the video short and every later word out of sync,
        # and nothing else here notices (2026-10-19: a 12.4s clip whose video ended at 7.8s).
        r = subprocess.run([ff, "-hide_banner", "-i", out, "-map", "0:v", "-vf", "showinfo", "-f", "null", "-"],
                           capture_output=True, text=True)
        ts = re.findall(r"pts_time:([\d.]+)", r.stderr)
        if ts and float(ts[-1]) < total - 0.2:
            print(f"  ⚠ the picture ends at {float(ts[-1]):.2f}s but the clip runs {total:.2f}s: "
                  f"video and sound are out of step. Don't ship this one")
    shutil.rmtree(tmp, ignore_errors=True)


def main():
    a = sys.argv[1:]
    cmds = {"ffmpeg": ((0,), lambda: print(ffmpeg_path())), "fetch": ((4,), cmd_fetch), "vtt": ((2,), cmd_vtt),
            "transcript": ((1, 2), cmd_transcript), "words": ((3,), cmd_words), "levels": ((3,), cmd_levels),
            "frame": ((3,), cmd_frame), "cuts": ((1, 2), cmd_cuts), "render": ((1,), cmd_render)}
    if not a or a[0] not in cmds or len(a) - 1 not in cmds[a[0]][0]:
        print(__doc__); sys.exit(1)
    cmds[a[0]][1](*a[1:])


if __name__ == "__main__":
    main()
