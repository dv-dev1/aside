# aside

**Live subtitles and reply suggestions for meetings in a language you are still learning.**

An aside: the line only you can hear. A thin bar at the bottom of your screen shows what the
other person just said — in English as they speak it, in Portuguese once the sentence lands —
and keeps three short replies ready for when you freeze.

Your meeting audio never leaves your machine. Transcription runs locally on the integrated GPU.
Only the transcribed text is sent out, and only to translate and to suggest.

## Why it works in every meeting app

It does not talk to Meet, Zoom or Teams. It listens to the PipeWire sink monitor — the audio
leaving your headphones. Your own voice goes to the microphone, not to the sink, so the
subtitle is the other side only, for free.

## What it sounds like

```
$ python3 -m aside.stt --arquivo tests/data/jfk.wav --marcos
 0.72s  And so, my fellow Americ
 0.85s  And so, my fellow Americans
 1.38s  And so, my fellow Americans, ask
 1.90s  And so, my fellow Americans, ask not
 2.54s  And so, my fellow Americans, ask not what your country
 final  And so, my fellow Americans, ask not what your country can do for you.
        Ask what you can do for your country.
```

## Why not Whisper

Whisper pads every clip to 30 seconds before processing, so a 2-second fragment costs almost
as much as an 11-second one. Measured on an Intel i5-1135G7 with Iris Xe, same 2s clip:

| engine | time | text |
| --- | --- | --- |
| Parakeet local, Vulkan | 0.32s | `And so, my fellow Americans.` |
| whisper tiny.en local | 0.71s | `And so my fellow American` |
| gpt-4o-mini-transcribe, cloud | 1.03s | `And so, my fellow Americans...` |
| whisper small local | 3.60s | `And so my fellow Americans` |

## Install

```bash
pip install -e '.[dev]'
python3 -m aside
```

First run downloads the Parakeet model (516 MB) and two fonts into `~/.local/share/aside`.
Set `OPENAI_API_KEY` for translation and suggestions; without it the English subtitle still runs.

## One thing you do by hand

GNOME's Mutter does not implement `zwlr_layer_shell_v1`, so no application can put itself on
top. Open the window menu with Alt+Space and tick **Always on Top**, once per session.

## License

MIT
