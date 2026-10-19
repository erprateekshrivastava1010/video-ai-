import argparse
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from engine import (
    TTSEngine,
    AudioAnalyzer,
    FacialAnimator,
    GestureEngine,
    VideoRenderer,
    AssetFactory
)

def main():
    parser = argparse.ArgumentParser(description="HeyGen Local Studio - CLI Video Generator")
    parser.add_argument("--script", type=str, required=True, help="Text script for avatar to speak")
    parser.add_argument("--avatar", type=str, default="sophia", help="Avatar ID (sophia, alex, marcus, emma)")
    parser.add_argument("--voice", type=str, default="en-us-female", help="Voice ID")
    parser.add_argument("--emotion", type=str, default="warm", choices=["warm", "neutral", "enthusiastic", "professional", "thoughtful"])
    parser.add_argument("--gesture", type=str, default="auto", choices=["auto", "dynamic", "presentation", "subtle", "off"])
    parser.add_argument("--intensity", type=float, default=1.0, help="Gesture intensity (0.5 to 1.5)")
    parser.add_argument("--bg", type=str, default="modern_office.jpg", help="Background image filename")
    parser.add_argument("--resolution", type=str, default="1280x720", choices=["1280x720", "720x1280"])
    parser.add_argument("--output", type=str, default="output/heygen_cli_video.mp4", help="Output MP4 file path")

    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "=" * 60)
    print("🎬 HeyGen Local Studio - CLI Video Synthesizer")
    print("=" * 60)
    print(f"Script:     '{args.script}'")
    print(f"Avatar:     {args.avatar}")
    print(f"Voice:      {args.voice}")
    print(f"Emotion:    {args.emotion}")
    print(f"Gestures:   {args.gesture} ({args.intensity}x)")
    print(f"Output:     {args.output}\n")

    # Ensure assets exist
    factory = AssetFactory(base_dir)
    factory.ensure_default_assets()

    # Step 1: TTS
    print("1/5 Synthesizing audio speech...")
    tts = TTSEngine()
    wav_path = os.path.join(output_dir, "temp_cli_speech.wav")
    tts.synthesize(args.script, voice_id=args.voice, output_wav_path=wav_path)

    # Step 2: Acoustic Prosody Analysis
    print("2/5 Extracting acoustic prosody & phoneme-to-viseme timing...")
    analyzer = AudioAnalyzer(fps=30)
    audio_data = analyzer.analyze_wav(wav_path)
    print(f"    Duration: {audio_data['duration']:.2f}s | Total Frames: {audio_data['total_frames']} | Stress Beats: {len(audio_data['stress_peaks'])}")

    # Step 3: Facial Animation Stream
    print("3/5 Generating lip-sync, micro-expressions & eye-blinks...")
    facial = FacialAnimator(fps=30)
    anim_stream = facial.generate_animation_stream(audio_data, emotion=args.emotion)

    # Step 4: Articulated Hand Kinematics
    print("4/5 Scheduling kinematic hand gestures...")
    gestures = GestureEngine(fps=30)
    gest_stream = gestures.schedule_gestures(audio_data, gesture_mode=args.gesture, intensity=args.intensity)

    # Step 5: Multi-Layer Video Compositing
    print("5/5 Rendering multi-layer video & encoding H.264/AAC...")
    w, h = (1280, 720) if args.resolution == "1280x720" else (720, 1280)
    renderer = VideoRenderer(base_dir, fps=30)
    
    t0 = time.time()
    renderer.render_video(
        avatar_id=args.avatar,
        background_file=args.bg,
        audio_wav=wav_path,
        animation_stream=anim_stream,
        gesture_stream=gest_stream,
        output_mp4=args.output,
        width=w,
        height=h
    )
    dur = time.time() - t0

    if os.path.exists(wav_path):
        os.remove(wav_path)

    print(f"\n🎉 Video generated successfully in {dur:.2f}s!")
    print(f"📁 Saved to: {os.path.abspath(args.output)}\n")

if __name__ == "__main__":
    main()
