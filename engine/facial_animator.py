import math
import random
import numpy as np
import cv2

class FacialAnimator:
    """
    Synthesizes frame-by-frame facial geometry, lip-sync visemes,
    micro-expressions, eye-blinks, gaze saccades, and head bobbing.
    """

    def __init__(self, fps: int = 30):
        self.fps = fps
        self.rng = random.Random(42)

    def generate_animation_stream(self, audio_data: dict, emotion: str = "warm"):
        """
        Takes audio analysis output and generates frame-by-frame animation transforms:
        - mouth_deform: (dx_corners, dy_jaw, open_ratio, round_ratio, smile_bias)
        - eye_blink: float 0.0 (fully open) to 1.0 (fully closed)
        - gaze_offset: (dx, dy)
        - eyebrow_offset_y: float
        - head_pose: (pitch, yaw, roll, tx, ty)
        """
        frames = audio_data["frames"]
        total_frames = len(frames)
        stress_peaks = set(audio_data.get("stress_peaks", []))

        # 1. Schedule natural eye blinks (every ~90-130 frames + near sentence pauses)
        blink_curve = np.zeros(total_frames, dtype=np.float32)
        frame_idx = 20
        while frame_idx < total_frames - 15:
            # interval 2.5s to 4.5s
            interval = int(self.fps * self.rng.uniform(2.5, 4.2))
            blink_start = frame_idx + interval
            if blink_start >= total_frames - 10:
                break

            # If there's a silence or pause nearby, snap blink to the pause
            search_window = range(max(0, blink_start - 15), min(total_frames, blink_start + 15))
            for sw in search_window:
                if frames[sw]["is_silent"]:
                    blink_start = sw
                    break

            blink_duration = int(self.fps * 0.22)  # ~6-7 frames
            for b in range(blink_duration):
                t = b / float(blink_duration)
                if t < 0.4:
                    val = (t / 0.4) ** 1.8
                else:
                    val = (1.0 - (t - 0.4) / 0.6) ** 1.5
                idx = blink_start + b
                if idx < total_frames:
                    blink_curve[idx] = max(blink_curve[idx], float(val))

            frame_idx = blink_start + blink_duration

        # 2. Gaze saccades (subtle subconscious eye motion)
        gaze_offsets = []
        cur_gx, cur_gy = 0.0, 0.0
        gaze_timer = 0
        for i in range(total_frames):
            if gaze_timer <= 0:
                cur_gx = self.rng.uniform(-1.5, 1.5)
                cur_gy = self.rng.uniform(-1.0, 1.0)
                gaze_timer = int(self.fps * self.rng.uniform(1.2, 3.0))
            else:
                gaze_timer -= 1
            gaze_offsets.append((cur_gx, cur_gy))

        # 3. Emotion parameters
        emotion_presets = {
            "neutral": {"smile": 0.05, "brow": 0.0, "nod_intensity": 1.0},
            "warm": {"smile": 0.22, "brow": 0.08, "nod_intensity": 1.1},
            "enthusiastic": {"smile": 0.38, "brow": 0.25, "nod_intensity": 1.4},
            "professional": {"smile": 0.10, "brow": 0.05, "nod_intensity": 0.9},
            "thoughtful": {"smile": 0.02, "brow": -0.05, "nod_intensity": 0.8},
        }
        emo = emotion_presets.get(emotion.lower(), emotion_presets["warm"])

        # 4. Generate frame-by-frame transforms
        animation_stream = []
        head_nod_phase = 0.0

        for i, f in enumerate(frames):
            # Eyebrow reaction to pitch & prosodic stress
            stress = f["stress"]
            pitch_norm = f["pitch_norm"]
            eyebrow_lift = (pitch_norm * 0.6 + stress * 0.4) * 8.0 + emo["brow"] * 6.0

            # Mouth deformation
            m_open = f["mouth_open"]
            m_wide = f["mouth_wide"]
            m_round = f["mouth_round"]
            lip_press = f["lip_press"]

            # Head motion: subtle continuous sinusoidal idle sway + nod on stress
            sway_x = math.sin(i * 0.04) * 1.5
            sway_y = math.cos(i * 0.035) * 1.2
            tilt_angle = math.sin(i * 0.025) * 0.8  # degrees

            # Stress nod
            if i in stress_peaks or stress > 0.6:
                nod_y = math.sin(stress * math.pi) * 3.5 * emo["nod_intensity"]
            else:
                nod_y = 0.0

            animation_stream.append({
                "frame_idx": i,
                "time": f["time"],
                "blink": float(blink_curve[i]),
                "gaze": gaze_offsets[i],
                "eyebrow_y": float(eyebrow_lift),
                "mouth": {
                    "open": float(m_open),
                    "wide": float(m_wide),
                    "round": float(m_round),
                    "press": float(lip_press),
                    "smile": float(emo["smile"])
                },
                "head": {
                    "dx": sway_x,
                    "dy": sway_y + nod_y,
                    "angle": tilt_angle
                }
            })

        return animation_stream
