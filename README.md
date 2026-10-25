# /clip

*Pull a short captioned clip out of something already recorded.*

---

## What it does

You point the AI you work with at a long video (a podcast episode on YouTube, a class or call you recorded) and tell it roughly which moment you want to highlight. Together you find the exact start and end, and it renders a clean clip with the captions burned in: 16:9 for LinkedIn or a landing page, 9:16 for Reels and Shorts, or both.

**It adds nothing on top.** No B-roll, no music, no generated video, no motion graphics. Only the people on screen, their own words, and captions. It's for clipping and curating things that resonate so they're easier to share. (Once you have a solid clip, feel free to add photos, title cards, etc., if you want; the AI can help. Think of this as a basic recipe to adapt to your own taste.)

The work splits in two: a script (`clip.py`) downloads the slice you need, reads word timings, measures where the pauses are, and renders. The judgment stays with you: which moment, where exactly to cut, which layout, whether it lands. The AI can check timing and framing on stills, but it can't watch or hear the result so your playback review is key.

---

## What you'll need

- **Claude Code** (in the terminal, or the Code tab in the Claude Desktop app), **or other agentic AI**. This skill runs a script, so it needs an AI that can run commands on your computer.
- **Python 3.10 or newer**
- **yt-dlp** (for YouTube videos)
- **ffmpeg**, or **uv** so the script can fetch its own copy (~50 MB, nothing installed system-wide)

You don't need to set these up first. The first time you use it, the AI checks what's there and tells you exactly what it would install before installing anything. No Homebrew required. Built and tested on macOS (captions use macOS's built-in fonts); on Linux, the skill says what to change. Windows is untested.

---

## Getting started

**Get the folder:** clone it (`git clone https://github.com/lsnackerman/raw-clauding-clip.git`), or on GitHub click **Code → Download ZIP** and unzip it. Or ask Claude Code to do these steps for you.

**In Claude Code:** link the folder into your project so it's available as `/clip`:

```bash
mkdir -p .claude/skills
ln -sfn "/path/to/raw-clauding-clip" ".claude/skills/clip"
```

Run it from your project folder, and replace `/path/to/raw-clauding-clip` with wherever the folder is. The link points at that folder, so updating it (`git pull`) updates the skill.

**Or copy it instead.** As it works, the AI adds new layouts to `layouts.md` and new lessons to `learnings.md`. With a link, those additions land in the downloaded folder, where your next update can collide with them. If you'd rather the files be yours to grow, copy the folder to `.claude/skills/clip` instead of linking it.

Then:

```
/clip https://youtube.com/watch?v=... the part where she explains why she started
```

or point it at a recording on your computer and riff from there.

**Another agent?** Point it at `SKILL.md` and tell it which video and which moment. It'll follow the steps from there.

---

## What's inside

| File | What it is |
|---|---|
| `SKILL.md` | The steps the AI follows, start to finish |
| `clip.py` | The script: fetch, word timings, loudness, scene cuts, render |
| `layouts.md` | Where things sit in the frame for a few shows and a Zoom screen share, as starting points; the AI adds new ones as it measures them |
| `learnings.md` | Why each step is there: every one came from a clip that went wrong |

Pro-tip: keep the spec (the JSON recipe) beside each clip you make. It's the exact record of the clip, so you can fix a caption or re-render later, even on another machine.

---

MIT licensed: use it, change it, share it.

*Built with real clips. More skills for thinking with AI: [raw-clauding-skills](https://github.com/lsnackerman/raw-clauding-skills).*
