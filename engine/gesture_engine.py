import math
import random
import numpy as np

class GestureEngine:
    """
    Kinematic Gesture Engine:
    Translates acoustic emphasis, cadence, and script rhythm into
    articulated human arm and hand gestures following natural gesture phases:
    Preparation -> Stroke (Apex) -> Retraction.
    """

    GESTURE_TYPES = [
        "open_palm_right",
        "open_palm_left",
        "two_hands_open",
        "point_emphasis_right",
        "counting_pinch",
        "chest_touch",
        "subtle_wave"
    ]

    def __init__(self, fps: int = 30):
        self.fps = fps
        self.rng = random.Random(1337)

    def schedule_gestures(self, audio_data: dict, gesture_mode: str = "auto", intensity: float = 1.0):
        """
        Plans hand and arm keyframes across the timeline.
        Returns a frame-by-frame list of hand kinematics:
        - left_hand: {active, gesture_type, x, y, angle, scale, alpha}
        - right_hand: {active, gesture_type, x, y, angle, scale, alpha}
        """
        total_frames = audio_data["total_frames"]
        frames = audio_data["frames"]
        stress_peaks = audio_data.get("stress_peaks", [])

        if gesture_mode == "off":
            return [self._resting_hands_frame(i) for i in range(total_frames)]

        # Determine gesture frequency
        if gesture_mode == "dynamic":
            min_gap_sec = 1.8
        elif gesture_mode == "subtle":
            min_gap_sec = 4.0
        elif gesture_mode == "presentation":
            min_gap_sec = 2.5
        else:  # auto
            min_gap_sec = 2.8

        min_gap_frames = int(self.fps * min_gap_sec)

        # Select candidate gesture trigger frames
        selected_triggers = []
        last_frame = -min_gap_frames

        # Prioritize stress peaks
        for peak in stress_peaks:
            if peak - last_frame >= min_gap_frames and peak < total_frames - int(self.fps * 1.5):
                selected_triggers.append(peak)
                last_frame = peak

        # If speech has few peaks (e.g. continuous smooth speech), space gestures evenly
        if len(selected_triggers) == 0 and total_frames > int(self.fps * 2.0):
            interval = int(self.fps * 3.5)
            curr = interval
            while curr < total_frames - int(self.fps * 1.5):
                selected_triggers.append(curr)
                curr += interval

        # Build scheduled gesture events
        scheduled_events = []
        for trig in selected_triggers:
            # Decide gesture type
            g_type = self.rng.choice(self.GESTURE_TYPES)
            prep_dur = int(self.fps * self.rng.uniform(0.35, 0.50))
            stroke_dur = int(self.fps * self.rng.uniform(0.50, 0.85))
            retract_dur = int(self.fps * self.rng.uniform(0.40, 0.60))

            start_f = max(0, trig - prep_dur)
            apex_start_f = trig
            apex_end_f = apex_start_f + stroke_dur
            end_f = min(total_frames, apex_end_f + retract_dur)

            scheduled_events.append({
                "type": g_type,
                "start": start_f,
                "apex_start": apex_start_f,
                "apex_end": apex_end_f,
                "end": end_f
            })

        # Generate frame-by-frame kinematics
        timeline = []
        for i in range(total_frames):
            frame_data = self._resting_hands_frame(i)

            # Check if any event is active at this frame
            for ev in scheduled_events:
                if ev["start"] <= i <= ev["end"]:
                    self._apply_gesture_kinematics(frame_data, ev, i, intensity)
                    break

            timeline.append(frame_data)

        return timeline

    def _resting_hands_frame(self, frame_idx: int):
        """Default natural presenter resting hand positions."""
        # Gentle micro-breathing sway
        sway = math.sin(frame_idx * 0.05) * 1.2
        return {
            "left_hand": {
                "active": False,
                "gesture_type": "rest",
                "x_norm": 0.36,
                "y_norm": 0.90 + sway * 0.002,
                "angle": 12.0,
                "scale": 1.0,
                "alpha": 0.0
            },
            "right_hand": {
                "active": False,
                "gesture_type": "rest",
                "x_norm": 0.64,
                "y_norm": 0.90 + sway * 0.002,
                "angle": -12.0,
                "scale": 1.0,
                "alpha": 0.0
            }
        }

    def _apply_gesture_kinematics(self, frame_data: dict, ev: dict, cur_f: int, intensity: float):
        """Calculates trajectory curve using smooth cubic easing."""
        g_type = ev["type"]
        start_f = ev["start"]
        apex_s = ev["apex_start"]
        apex_e = ev["apex_end"]
        end_f = ev["end"]

        # Calculate progress t (0.0 to 1.0) and phase
        if cur_f < apex_s:
            # Preparation phase: rising up
            t = (cur_f - start_f) / max(1, (apex_s - start_f))
            # Smoothstep easing
            weight = t * t * (3 - 2 * t)
        elif cur_f <= apex_e:
            # Stroke/Hold phase: subtle hold with gentle emphasis pulse
            hold_t = (cur_f - apex_s) / max(1, (apex_e - apex_s))
            pulse = math.sin(hold_t * math.pi) * 0.08
            weight = 1.0 + pulse
        else:
            # Retraction phase: lowering back down
            t = (cur_f - apex_e) / max(1, (end_f - apex_e))
            weight = 1.0 - (t * t * (3 - 2 * t))

        weight = max(0.0, min(1.2, weight)) * intensity

        # Assign motion to left, right, or both hands
        if "right" in g_type or g_type in ["counting_pinch", "subtle_wave"]:
            h = frame_data["right_hand"]
            h["active"] = True
            h["gesture_type"] = g_type
            h["alpha"] = min(1.0, weight)
            # Lift hand up towards chest/presentation space (y: 0.90 -> 0.68)
            h["x_norm"] = 0.64 + 0.08 * weight
            h["y_norm"] = 0.90 - 0.24 * weight
            h["angle"] = -12.0 - 15.0 * weight
            h["scale"] = 1.0 + 0.05 * weight

        elif "left" in g_type or g_type == "chest_touch":
            h = frame_data["left_hand"]
            h["active"] = True
            h["gesture_type"] = g_type
            h["alpha"] = min(1.0, weight)
            h["x_norm"] = 0.36 - 0.08 * weight
            h["y_norm"] = 0.90 - 0.24 * weight
            h["angle"] = 12.0 + 15.0 * weight
            h["scale"] = 1.0 + 0.05 * weight

        elif g_type == "two_hands_open":
            # Both hands gesture outwards symmetrically
            for key, sign in [("left_hand", -1), ("right_hand", 1)]:
                h = frame_data[key]
                h["active"] = True
                h["gesture_type"] = g_type
                h["alpha"] = min(1.0, weight)
                base_x = 0.50 + sign * 0.14
                h["x_norm"] = base_x + sign * (0.08 * weight)
                h["y_norm"] = 0.90 - 0.22 * weight
                h["angle"] = sign * (12.0 + 14.0 * weight)
                h["scale"] = 1.0 + 0.04 * weight
