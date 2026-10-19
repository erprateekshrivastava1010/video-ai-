# 🎭 HeyGen Local Studio — AI Avatar, Lip-Sync & Hand Gesture Video Engine

A fully local, GPU/CPU-optimized replica of **HeyGen AI's video generation engine**. Create realistic talking avatar videos with synchronized lip-sync, micro-expressions (eye-blinks, gaze saccades, eyebrow dynamics, head tilts), and speech-driven hand gestures—**running 100% locally with zero external API dependencies**.

---

## 🔬 How HeyGen AI Works: Reverse Engineering & Core Principles

HeyGen's video generation technology moves far beyond simple static image cutouts or generic 2D morphs. It combines **generative acoustic decomposition, 3D Morphable Model (3DMM) viseme kinematics, neural micro-expressions, and pose-guided kinematic state machines**.

```
[ Text Script ]
      │
      ▼
[ Text-to-Speech (TTS) Engine ] ──> Neural Audio Waveform (16kHz PCM)
      │
      ├──> [ Acoustic Prosody & Pitch Analysis ]
      │         │
      │         ├──> Energy Envelope (RMS) & Band Energy Splits
      │         ├──> F0 Fundamental Pitch Contour
      │         └──> Speech Stress Peak & Pause Detection
      │
      ├──> [ Audio-to-Viseme Lip Sync Synthesizer ]
      │         │
      │         ├──> Jaw drop / mouth openness deformation
      │         ├──> Lip spreading (smile/fricatives) & rounding (pucker)
      │         ├──> Oral cavity depth & teeth/tongue rendering
      │         └──> Co-articulation temporal smoothing
      │
      ├──> [ Expressive Micro-Moments Engine ]
      │         │
      │         ├──> Poisson Eye Blinking (timed to speech pauses)
      │         ├──> Gaze Saccades (subtle subconscious pupil shifts)
      │         ├──> Pitch-reactive Eyebrow elevation (questions & emphasis)
      │         └──> Conversational Head Nodding on vocal beats
      │
      └──> [ Articulated Hand Gesture Kinematics ]
                │
                ├──> Preparation Phase (0.3–0.5s ease-in from rest)
                ├──> Stroke / Apex Phase (0.5–0.8s lock with stress peak)
                └──> Retraction Phase (0.4–0.6s ease-out back to rest)
                      │
                      ▼
[ Multi-Layer Neural Video Compositor & FFmpeg H.264/AAC Encoder ] ──> Final MP4 Video
```

### 1. Acoustic Phonetic Analysis & Prosody Decomposition
HeyGen uses audio as the primary driving signal. Incoming audio is decomposed into:
- **Phonemes & Formants ($F_1, F_2$):** Distinguishing bilabial closures (`M`, `B`, `P`), dental fricatives (`F`, `V`, `TH`), high-frequency sibilants (`S`, `SH`), and open/round vowels (`AA`, `EE`, `OO`).
- **Acoustic Energy & Pitch ($F_0$):** Detecting vocal intensity and pitch inflections. When a speaker raises their voice pitch or stresses an important word, this informs both facial micro-expressions and arm gestures.

### 2. Audio-Driven Lip Sync & Micro-Moments
To overcome the "uncanny valley":
- **Viseme Morphing:** Lower lip descent, upper lip positioning, lip corner stretching, and inner oral cavity depth are computed with continuous cubic spline smoothing to avoid robotic transitions.
- **Natural Eye Blinking:** Blinks occur every 2.5–4.5 seconds with non-linear easing ($t^{1.8}$ dip, $(1-t)^{1.5}$ rise) and automatically snap to natural speech pauses.
- **Eye Gaze Saccades:** Continuous $1-2$px micro-shifts mimic real human ocular behavior.
- **Eyebrow Dynamics:** Driven by pitch peaks and emotional states (Warm, Enthusiastic, Corporate, Thoughtful).

### 3. Kinematic Hand Gesture Engine
In human speech, gestures are not random twitches; they follow **McNeill’s Gesture Dimensions**:
- **Preparation Phase:** The hand lifts smoothly from the resting posture toward the presentation space.
- **Stroke / Apex:** The maximum expansion of the gesture (open palms, pointing, or framing) aligns precisely with the vocal emphasis peak.
- **Retraction:** The hand smoothly returns to a relaxed presenter resting position.

### 4. Multi-Layer Video Compositing
- Background Canvas (Studio, Office, Tech, Green Screen, Custom)
- Avatar Torso & Postural Sway
- Articulated Hand & Arm Kinematics with Drop Shadow
- Dynamic Face & Lip-Sync Layer
- FFmpeg H.264/AAC stream muxing with web-optimized `+faststart`.

---

## ✨ Features

- 🎙️ **Multi-Engine TTS:** Works online via Google TTS or 100% offline via native Windows Speech (pyttsx3/SAPI).
- 🧑‍💼 **Built-in Studio Avatars:** Sophia (Corporate Executive), Alex (Tech Presenter), Marcus (Creative Host), Emma (UGC Creator).
- 📸 **Custom Avatar Photo Rigging:** Upload any portrait photo—the engine automatically detects face, eyes, and mouth landmarks and animates it!
- 🎬 **Customizable Backgrounds:** Modern Glass Office, Blue Studio Spotlight, Tech Dark Grid, Pastel Gradient, or Pure Green Screen for Chroma Key in Premiere/CapCut/DaVinci.
- 📐 **Multiple Formats:** 16:9 Landscape (YouTube/Presentations) or 9:16 Portrait (TikTok/Reels/Shorts).
- 🖥️ **Modern Web Studio:** HeyGen-style glassmorphic studio UI with real-time word counter, audio preview, progress telemetry, and instant MP4 downloads.
- ⚡ **CLI Automation:** Command-line tool for automated batch generation.

---

## 🚀 Quick Start

### 1. Installation
Clone this repository and install dependencies:
```bash
git clone https://github.com/erprateekshrivastava1010/video-ai-.git
cd video-ai-
pip install -r requirements.txt
```

### 2. Launch the Web Studio
On Windows, double-click `run.bat` or run:
```bash
python app.py
```
Open your browser at:
👉 **[http://localhost:7860](http://localhost:7860)**

### 3. CLI Mode (Command Line)
Generate videos directly without the UI:
```bash
python generate_cli.py --script "Welcome to our local HeyGen AI Studio. Creating video avatars locally!" --avatar sophia --emotion warm --gesture auto --output output/my_video.mp4
```

---

## 🌐 Live Tunneling (Shareable Public URL)

To share your local studio live with others or access it remotely, run any of the following free tunnels:

### Option A: LocalTunnel (Instant)
```bash
npx localtunnel --port 7860
```
This gives you an instant `https://xxxx.loca.lt` URL!

### Option B: Cloudflare Tunnel (Recommended)
```bash
cloudflared tunnel --url http://localhost:7860
```
This gives a free, zero-config `https://xxxx.trycloudflare.com` URL.

### Option C: Ngrok
```bash
ngrok http 7860
```

---

## 📂 Project Architecture

```
video-ai-/
├── app.py                      # FastAPI Web Server & API backend
├── generate_cli.py             # Command-Line Video Synthesizer
├── run.bat                     # Windows 1-Click Launcher
├── requirements.txt            # Python dependencies
├── engine/
│   ├── __init__.py
│   ├── tts_engine.py           # Multi-engine TTS (gTTS, pyttsx3, SAPI)
│   ├── audio_analyzer.py       # Prosody, pitch & phoneme-to-viseme analysis
│   ├── facial_animator.py      # Lip-sync, blinks, gaze & expressions
│   ├── gesture_engine.py       # Articulated hand gesture kinematics
│   ├── video_renderer.py       # Frame compositor & FFmpeg MP4 encoder
│   └── asset_factory.py        # Avatar generator & custom photo rigger
├── static/
│   ├── index.html              # HeyGen Studio Frontend UI
│   ├── css/style.css           # Glassmorphism dark studio styling
│   └── js/app.js               # Frontend application controller
└── output/                     # Generated videos and audio files
```

---

## 📄 License
MIT License. Built for educational, research, and creative AI avatar synthesis.
