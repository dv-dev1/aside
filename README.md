# aside

**Live subtitles and reply suggestions for meetings in a language you are still learning.**

An aside: the line only you can hear. A small bar floating in the top-right corner of your
screen shows what the other person just said — in English as they speak, in Portuguese right
behind it — and keeps three short replies ready for when you freeze.

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
To open it from the app grid without exporting anything, store the key once in the GNOME keyring:
`secret-tool store --label='aside OpenAI' service aside`.

## Interview mode

Drop Markdown files into `~/.config/aside/` — your profile, the job description, notes about
who you are meeting. They are read at startup and turn the suggestions into first-person answers
grounded only in those facts. They live outside the repository on purpose: they carry personal
data, and they are sent to the model with every suggestion, never committed.

## How it stays on top

GNOME's Mutter does not implement `zwlr_layer_shell_v1`, so no Wayland application can put
itself above the others. `aside` runs under XWayland, where the protocol is EWMH, and asks for
`_NET_WM_STATE_ABOVE` with a ClientMessage to the root window. Writing the property directly
does not work: Mutter discards it.

## License

MIT
