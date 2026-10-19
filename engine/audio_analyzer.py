import wave
import numpy as np
import scipy.signal

class AudioAnalyzer:
    """
    Acoustic Feature & Prosody Decomposition Engine:
    Translates raw speech waveforms into frame-by-frame mouth visemes,
    emotional prosody metrics, pitch contours, and gesture emphasis triggers.
    """

    def __init__(self, fps: int = 30):
        self.fps = fps

    def analyze_wav(self, wav_path: str):
        """
        Processes a 16kHz mono WAV file and extracts frame-aligned animation parameters.
        Returns a dict containing:
        - duration: float seconds
        - total_frames: int
        - frames: list of FrameFeatures
        - stress_peaks: list of frame indices with strong acoustic emphasis (triggers for gestures)
        """
        with wave.open(wav_path, "r") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw_bytes = wf.readframes(n_frames)

        # Convert to float numpy array normalized between -1.0 and 1.0
        if sampwidth == 2:
            audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampwidth == 4:
            audio = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            audio = np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

        if n_channels > 1:
            audio = audio.reshape(-1, n_channels).mean(axis=1)

        duration = len(audio) / framerate
        total_video_frames = max(1, int(round(duration * self.fps)))

        # Frame windowing for analysis
        samples_per_video_frame = framerate / self.fps
        win_size = int(samples_per_video_frame * 1.5)  # slight overlap for smooth analysis
        
        frame_features = []
        raw_energies = []
        raw_pitches = []

        for i in range(total_video_frames):
            center = int(i * samples_per_video_frame)
            start = max(0, center - win_size // 2)
            end = min(len(audio), center + win_size // 2)
            chunk = audio[start:end]

            if len(chunk) < 64:
                frame_features.append({
                    "frame_idx": i,
                    "time": i / self.fps,
                    "rms": 0.0,
                    "mouth_open": 0.0,
                    "mouth_wide": 0.0,
                    "mouth_round": 0.0,
                    "lip_press": 0.0,
                    "pitch_norm": 0.0,
                    "stress": 0.0,
                    "is_silent": True
                })
                raw_energies.append(0.0)
                raw_pitches.append(0.0)
                continue

            # 1. RMS Energy
            rms = float(np.sqrt(np.mean(chunk**2)))
            raw_energies.append(rms)

            # 2. FFT Spectral Analysis
            fft = np.abs(np.fft.rfft(chunk * np.hanning(len(chunk))))
            freqs = np.fft.rfftfreq(len(chunk), d=1.0 / framerate)

            total_spec_power = np.sum(fft) + 1e-9
            centroid = float(np.sum(freqs * fft) / total_spec_power)

            # Band energy splits:
            # Low: 100-800 Hz (Formant F1 - vowel openness / jaw drop)
            # Mid: 800-2500 Hz (Formant F2 - front/back tongue position, smile/spread)
            # High: 2500-7500 Hz (Fricatives, sibilants 's', 'sh', 'th', 'f')
            low_mask = (freqs >= 100) & (freqs < 800)
            mid_mask = (freqs >= 800) & (freqs < 2500)
            high_mask = (freqs >= 2500) & (freqs < 7500)

            low_power = np.sum(fft[low_mask]) / total_spec_power
            mid_power = np.sum(fft[mid_mask]) / total_spec_power
            high_power = np.sum(fft[high_mask]) / total_spec_power

            # 3. Simple Autocorrelation Pitch Estimation (F0 between 75 Hz and 400 Hz)
            min_lag = int(framerate / 400)
            max_lag = int(framerate / 75)
            pitch_val = 0.0
            if rms > 0.015 and len(chunk) > max_lag:
                corr = np.correlate(chunk, chunk, mode="full")
                corr = corr[len(corr)//2:]
                if max_lag < len(corr):
                    peak_lag = min_lag + np.argmax(corr[min_lag:max_lag])
                    pitch_val = framerate / peak_lag
            raw_pitches.append(pitch_val)

            frame_features.append({
                "frame_idx": i,
                "time": i / self.fps,
                "rms": rms,
                "centroid": centroid,
                "low_power": low_power,
                "mid_power": mid_power,
                "high_power": high_power,
                "pitch": pitch_val
            })

        # Temporal smoothing and normalization
        raw_energies = np.array(raw_energies)
        max_energy = np.percentile(raw_energies, 95) if len(raw_energies) > 0 else 1.0
        max_energy = max(max_energy, 0.02)
        norm_energies = np.clip(raw_energies / max_energy, 0.0, 1.0)

        # Smooth energy using Savitzky-Golay / moving window for natural co-articulation
        if len(norm_energies) > 7:
            smoothed_energies = scipy.signal.savgol_filter(norm_energies, 5, 2)
            smoothed_energies = np.clip(smoothed_energies, 0.0, 1.0)
        else:
            smoothed_energies = norm_energies

        # Detect stress peaks (syllables with local maxima in energy & pitch)
        peaks, _ = scipy.signal.find_peaks(smoothed_energies, height=0.35, distance=int(self.fps * 0.4))
        stress_peaks = [int(p) for p in peaks]

        final_frames = []
        for i, feat in enumerate(frame_features):
            n_energy = smoothed_energies[i]
            is_silent = n_energy < 0.06

            if is_silent:
                mouth_open = 0.0
                mouth_wide = 0.0
                mouth_round = 0.0
                lip_press = 0.0
            else:
                # Open mouth correlates with low/mid formant energy + loudness
                mouth_open = float(np.clip(n_energy * (1.1 * feat.get("low_power", 0.3) + 0.5), 0.0, 1.0))
                # Spread / smile ('ee', 'ai') correlates with mid-range energy
                mouth_wide = float(np.clip(feat.get("mid_power", 0.3) * 1.6 * n_energy, 0.0, 1.0))
                # Rounded ('oo', 'oh') correlates with low centroid + lower high_power
                mouth_round = float(np.clip(max(0.0, 0.7 - feat.get("centroid", 1500) / 3000.0) * n_energy * 1.5, 0.0, 1.0))
                # Bilabial press ('m', 'b', 'p') happens at energy dip preceding a burst
                lip_press = 1.0 - mouth_open if n_energy < 0.12 else 0.0

            # Pitch normalization
            p_val = feat.get("pitch", 0.0)
            pitch_norm = float(np.clip((p_val - 100.0) / 250.0, 0.0, 1.0)) if p_val > 0 else 0.0

            # Stress score (peak closeness)
            is_near_peak = min([abs(i - p) for p in stress_peaks]) if stress_peaks else 999
            stress_score = float(max(0.0, 1.0 - (is_near_peak / (self.fps * 0.25))))

            final_frames.append({
                "frame_idx": i,
                "time": feat["time"],
                "rms": float(feat["rms"]),
                "energy": float(n_energy),
                "mouth_open": mouth_open,
                "mouth_wide": mouth_wide,
                "mouth_round": mouth_round,
                "lip_press": lip_press,
                "pitch_norm": pitch_norm,
                "stress": stress_score,
                "is_silent": is_silent
            })

        return {
            "duration": duration,
            "total_frames": total_video_frames,
            "frames": final_frames,
            "stress_peaks": stress_peaks
        }
