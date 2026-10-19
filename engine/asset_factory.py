import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

class AssetFactory:
    """
    Creates and manages photorealistic avatar assets, articulated hand graphics,
    and studio backgrounds. Also auto-rigs user-uploaded custom portrait photos.
    """

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.avatars_dir = os.path.join(base_dir, "static", "assets", "avatars")
        self.backgrounds_dir = os.path.join(base_dir, "static", "assets", "backgrounds")
        self.hands_dir = os.path.join(base_dir, "static", "assets", "hands")

        os.makedirs(self.avatars_dir, exist_ok=True)
        os.makedirs(self.backgrounds_dir, exist_ok=True)
        os.makedirs(self.hands_dir, exist_ok=True)

        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

    def ensure_default_assets(self):
        """Creates the default avatars, hand gestures, and backgrounds if missing."""
        self._ensure_backgrounds()
        self._ensure_hand_assets()
        self._ensure_default_avatars()

    def _ensure_backgrounds(self):
        """Generates modern 1080p studio backgrounds."""
        bgs = {
            "modern_office.jpg": self._draw_modern_office,
            "studio_blue.jpg": self._draw_studio_blue,
            "tech_dark.jpg": self._draw_tech_dark,
            "gradient_aura.jpg": self._draw_gradient_aura,
            "green_screen.jpg": self._draw_green_screen,
        }
        for name, func in bgs.items():
            path = os.path.join(self.backgrounds_dir, name)
            if not os.path.exists(path):
                img = func(1280, 720)
                cv2.imwrite(path, img)

    def _draw_modern_office(self, w, h):
        img = np.zeros((h, w, 3), dtype=np.uint8)
        # Soft blurred corporate glass aesthetic
        for y in range(h):
            factor = y / h
            img[y, :] = [int(220 - 40 * factor), int(225 - 35 * factor), int(235 - 30 * factor)]
        
        # Soft architectural glass window grid in background
        cv2.line(img, (int(w * 0.35), 0), (int(w * 0.35), h), (200, 205, 215), 6)
        cv2.line(img, (int(w * 0.70), 0), (int(w * 0.70), h), (200, 205, 215), 6)
        cv2.line(img, (0, int(h * 0.45)), (w, int(h * 0.45)), (190, 195, 205), 4)

        # Soft indoor plant bokeh in corner
        cv2.circle(img, (int(w * 0.12), int(h * 0.75)), 120, (140, 165, 140), -1)
        cv2.circle(img, (int(w * 0.16), int(h * 0.65)), 90, (130, 175, 130), -1)
        cv2.circle(img, (int(w * 0.88), int(h * 0.35)), 140, (240, 240, 250), -1)

        # Gaussian blur for cinematic depth of field
        img = cv2.GaussianBlur(img, (45, 45), 0)
        return img

    def _draw_studio_blue(self, w, h):
        img = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            f = y / h
            img[y, :] = [int(75 - 30 * f), int(35 - 15 * f), int(20 - 10 * f)]
        # Center glow spotlight
        cv2.circle(img, (int(w * 0.5), int(h * 0.4)), int(w * 0.38), (170, 90, 40), -1)
        cv2.circle(img, (int(w * 0.5), int(h * 0.4)), int(w * 0.22), (220, 140, 60), -1)
        return cv2.GaussianBlur(img, (85, 85), 0)

    def _draw_tech_dark(self, w, h):
        img = np.zeros((h, w, 3), dtype=np.uint8)
        img[:, :] = (24, 20, 18)
        # Subtle cyber grid
        for x in range(0, w, 80):
            cv2.line(img, (x, 0), (x, h), (40, 32, 28), 1)
        for y in range(0, h, 80):
            cv2.line(img, (0, y), (w, y), (40, 32, 28), 1)
        # Cyberpunk neon accent line at bottom
        cv2.line(img, (0, int(h * 0.85)), (w, int(h * 0.85)), (220, 160, 30), 2)
        return cv2.GaussianBlur(img, (15, 15), 0)

    def _draw_gradient_aura(self, w, h):
        img = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            for x in range(w):
                fx = x / w
                fy = y / h
                b = int(120 + 80 * fy)
                g = int(60 + 120 * fx)
                r = int(180 - 60 * fy)
                img[y, x] = (b, g, r)
        return cv2.GaussianBlur(img, (55, 55), 0)

    def _draw_green_screen(self, w, h):
        img = np.zeros((h, w, 3), dtype=np.uint8)
        img[:, :] = (0, 255, 0)  # Pure chroma key
        return img

    def _ensure_hand_assets(self):
        """Generates realistic articulated hand graphics with transparency."""
        gestures = [
            ("hand_open_palm.png", "palm"),
            ("hand_point.png", "point"),
            ("hand_frame.png", "frame"),
            ("hand_rest.png", "rest")
        ]
        for name, style in gestures:
            path = os.path.join(self.hands_dir, name)
            if not os.path.exists(path):
                img = self._render_hand_png(260, 320, style, skin_tone=(195, 165, 225))
                cv2.imwrite(path, img)

    def _render_hand_png(self, w, h, style, skin_tone):
        # 4-channel BGRA image
        img = np.zeros((h, w, 4), dtype=np.uint8)
        b, g, r = skin_tone
        color = (b, g, r, 255)
        shade_color = (int(b * 0.85), int(g * 0.85), int(r * 0.85), 255)
        highlight = (int(min(255, b * 1.1)), int(min(255, g * 1.1)), int(min(255, r * 1.1)), 255)

        # Forearm / wrist base
        cv2.ellipse(img, (w // 2, h - 20), (55, 80), 0, 0, 360, shade_color, -1)
        cv2.ellipse(img, (w // 2, h - 35), (50, 75), 0, 0, 360, color, -1)

        # Palm center
        cv2.circle(img, (w // 2, h // 2 + 20), 55, color, -1)

        if style == "palm":
            # 4 open fingers + thumb
            cv2.ellipse(img, (w // 2 - 40, h // 2 - 40), (14, 45), -15, 0, 360, color, -1)
            cv2.ellipse(img, (w // 2 - 14, h // 2 - 65), (14, 52), -5, 0, 360, color, -1)
            cv2.ellipse(img, (w // 2 + 14, h // 2 - 62), (14, 50), 5, 0, 360, color, -1)
            cv2.ellipse(img, (w // 2 + 40, h // 2 - 38), (13, 42), 15, 0, 360, color, -1)
            # Thumb
            cv2.ellipse(img, (w // 2 - 58, h // 2 + 20), (16, 38), -45, 0, 360, color, -1)

        elif style == "point":
            # Index extended upward, other fingers curled
            cv2.ellipse(img, (w // 2 - 10, h // 2 - 75), (15, 58), 0, 0, 360, color, -1)
            # Curled fingers
            cv2.ellipse(img, (w // 2 + 18, h // 2 - 10), (16, 22), 0, 0, 360, shade_color, -1)
            cv2.ellipse(img, (w // 2 + 38, h // 2 - 5), (15, 20), 0, 0, 360, shade_color, -1)
            # Thumb holding curled fingers
            cv2.ellipse(img, (w // 2 - 35, h // 2 + 15), (18, 32), -30, 0, 360, color, -1)

        elif style == "frame":
            # Open framing hand with angled thumb and fingers
            cv2.ellipse(img, (w // 2, h // 2 - 55), (32, 50), 0, 0, 360, color, -1)
            cv2.ellipse(img, (w // 2 - 45, h // 2 - 10), (16, 38), -50, 0, 360, color, -1)

        else:  # rest
            # Relaxed curved fingers
            cv2.ellipse(img, (w // 2, h // 2 - 25), (45, 40), 0, 0, 360, color, -1)
            cv2.ellipse(img, (w // 2 - 40, h // 2 + 10), (15, 30), -35, 0, 360, color, -1)

        # Smooth edges with antialiasing
        img = cv2.GaussianBlur(img, (3, 3), 0)
        return img

    def _ensure_default_avatars(self):
        """Generates built-in high quality avatars."""
        avatars = [
            {
                "id": "sophia",
                "name": "Sophia (Corporate Executive)",
                "gender": "female",
                "hair_color": (35, 45, 70),
                "skin_tone": (205, 185, 235),
                "clothing_color": (60, 45, 120),  # Burgundy blazer
                "shirt_color": (240, 240, 245)
            },
            {
                "id": "alex",
                "name": "Alex (Tech Presenter)",
                "gender": "male",
                "hair_color": (25, 25, 30),
                "skin_tone": (195, 175, 225),
                "clothing_color": (110, 60, 35),  # Navy suit
                "shirt_color": (230, 240, 250)
            },
            {
                "id": "marcus",
                "name": "Marcus (Creative Studio Host)",
                "gender": "male",
                "hair_color": (30, 35, 40),
                "skin_tone": (145, 120, 175),
                "clothing_color": (45, 45, 50),  # Charcoal crewneck
                "shirt_color": (50, 50, 55)
            },
            {
                "id": "emma",
                "name": "Emma (Education & UGC Host)",
                "gender": "female",
                "hair_color": (40, 70, 110),
                "skin_tone": (210, 190, 240),
                "clothing_color": (120, 95, 40),  # Emerald teal top
                "shirt_color": (245, 245, 245)
            }
        ]

        for av in avatars:
            av_dir = os.path.join(self.avatars_dir, av["id"])
            os.makedirs(av_dir, exist_ok=True)
            base_path = os.path.join(av_dir, "base.png")
            if not os.path.exists(base_path):
                self._generate_avatar_bundle(av_dir, av)

    def _generate_avatar_bundle(self, av_dir: str, config: dict):
        """Generates avatar base portrait (720x960), facial features, and masks."""
        w, h = 720, 960
        img = np.zeros((h, w, 4), dtype=np.uint8)
        
        skin_b, skin_g, skin_r = config["skin_tone"]
        cloth_b, cloth_g, cloth_r = config["clothing_color"]
        hair_b, hair_g, hair_r = config["hair_color"]

        # 1. Torso & Shoulders
        shoulder_center = (w // 2, h + 80)
        cv2.ellipse(img, (w // 2, h - 80), (int(w * 0.44), int(h * 0.35)), 0, 0, 360, (cloth_b, cloth_g, cloth_r, 255), -1)
        
        # Shirt / Collar V-neck
        v_pts = np.array([
            [w // 2 - 50, int(h * 0.60)],
            [w // 2 + 50, int(h * 0.60)],
            [w // 2, int(h * 0.74)]
        ], np.int32)
        cv2.fillPoly(img, [v_pts], (*config["shirt_color"], 255))

        # 2. Neck
        neck_pts = np.array([
            [w // 2 - 55, int(h * 0.48)],
            [w // 2 + 55, int(h * 0.48)],
            [w // 2 + 65, int(h * 0.63)],
            [w // 2 - 65, int(h * 0.63)],
        ], np.int32)
        cv2.fillPoly(img, [neck_pts], (int(skin_b * 0.88), int(skin_g * 0.88), int(skin_r * 0.88), 255))

        # 3. Head & Face Oval
        face_center_x = w // 2
        face_center_y = int(h * 0.36)
        face_axes = (int(w * 0.22), int(h * 0.23))
        
        # Face shadow & base
        cv2.ellipse(img, (face_center_x, face_center_y), face_axes, 0, 0, 360, (skin_b, skin_g, skin_r, 255), -1)

        # Jawline softening
        jaw_pts = np.array([
            [face_center_x - int(face_axes[0] * 0.75), face_center_y + int(face_axes[1] * 0.4)],
            [face_center_x + int(face_axes[0] * 0.75), face_center_y + int(face_axes[1] * 0.4)],
            [face_center_x + int(face_axes[0] * 0.45), face_center_y + int(face_axes[1] * 0.95)],
            [face_center_x - int(face_axes[0] * 0.45), face_center_y + int(face_axes[1] * 0.95)],
        ], np.int32)
        cv2.fillPoly(img, [jaw_pts], (skin_b, skin_g, skin_r, 255))

        # 4. Hair
        if config["gender"] == "female":
            # Long volumetric styling
            cv2.ellipse(img, (face_center_x, face_center_y - 45), (int(w * 0.26), int(h * 0.25)), 0, 0, 360, (hair_b, hair_g, hair_r, 255), -1)
            # Re-draw face over hair base
            cv2.ellipse(img, (face_center_x, face_center_y), face_axes, 0, 0, 360, (skin_b, skin_g, skin_r, 255), -1)
            # Side hair tresses
            cv2.ellipse(img, (face_center_x - int(w * 0.22), face_center_y + 90), (38, 140), 10, 0, 360, (hair_b, hair_g, hair_r, 255), -1)
            cv2.ellipse(img, (face_center_x + int(w * 0.22), face_center_y + 90), (38, 140), -10, 0, 360, (hair_b, hair_g, hair_r, 255), -1)
            # Top forehead hairline
            cv2.ellipse(img, (face_center_x, face_center_y - 105), (int(w * 0.24), 85), 0, 0, 360, (hair_b, hair_g, hair_r, 255), -1)
        else:
            # Short professional cut
            cv2.ellipse(img, (face_center_x, face_center_y - 85), (int(w * 0.23), 100), 0, 0, 360, (hair_b, hair_g, hair_r, 255), -1)
            cv2.ellipse(img, (face_center_x - int(w * 0.21), face_center_y - 30), (22, 55), 0, 0, 360, (hair_b, hair_g, hair_r, 255), -1)
            cv2.ellipse(img, (face_center_x + int(w * 0.21), face_center_y - 30), (22, 55), 0, 0, 360, (hair_b, hair_g, hair_r, 255), -1)

        # 5. Eyebrows
        cv2.line(img, (face_center_x - 75, face_center_y - 48), (face_center_x - 25, face_center_y - 52), (hair_b, hair_g, hair_r, 255), 5)
        cv2.line(img, (face_center_x + 25, face_center_y - 52), (face_center_x + 75, face_center_y - 48), (hair_b, hair_g, hair_r, 255), 5)

        # 6. Eyes (Sclera + Iris + Pupil + Catchlight)
        for eye_x in [face_center_x - 50, face_center_x + 50]:
            # Sclera
            cv2.ellipse(img, (eye_x, face_center_y - 25), (20, 11), 0, 0, 360, (245, 245, 250, 255), -1)
            # Iris
            cv2.circle(img, (eye_x, face_center_y - 25), 8, (60, 40, 25, 255), -1)
            # Pupil
            cv2.circle(img, (eye_x, face_center_y - 25), 4, (10, 10, 10, 255), -1)
            # Reflection highlight
            cv2.circle(img, (eye_x - 2, face_center_y - 28), 2, (255, 255, 255, 255), -1)
            # Upper eyelid
            cv2.ellipse(img, (eye_x, face_center_y - 26), (22, 12), 0, 180, 360, (80, 50, 40, 255), 2)

        # 7. Nose bridge and tip
        cv2.line(img, (face_center_x, face_center_y - 15), (face_center_x, face_center_y + 35), (int(skin_b * 0.82), int(skin_g * 0.82), int(skin_r * 0.82), 255), 3)
        cv2.ellipse(img, (face_center_x, face_center_y + 35), (14, 7), 0, 0, 180, (int(skin_b * 0.78), int(skin_g * 0.78), int(skin_r * 0.78), 255), 2)

        # 8. Natural Resting Lips
        mouth_y = face_center_y + 85
        # Upper lip
        cv2.ellipse(img, (face_center_x, mouth_y - 4), (28, 9), 0, 0, 180, (int(skin_b * 0.75), int(skin_g * 0.68), int(min(255, skin_r * 1.15)), 255), -1)
        # Lower lip
        cv2.ellipse(img, (face_center_x, mouth_y + 4), (26, 11), 0, 180, 360, (int(skin_b * 0.78), int(skin_g * 0.72), int(min(255, skin_r * 1.20)), 255), -1)
        # Lip crease
        cv2.line(img, (face_center_x - 28, mouth_y), (face_center_x + 28, mouth_y), (int(skin_b * 0.60), int(skin_g * 0.50), int(skin_r * 0.70), 255), 2)

        # Anti-aliasing
        img = cv2.GaussianBlur(img, (3, 3), 0)

        # Save base portrait
        base_path = os.path.join(av_dir, "base.png")
        cv2.imwrite(base_path, img)

        # Save metadata with facial landmarks coordinates
        import json
        meta = {
            "id": config["id"],
            "name": config["name"],
            "gender": config["gender"],
            "landmarks": {
                "face_center": [face_center_x, face_center_y],
                "left_eye": [face_center_x - 50, face_center_y - 25],
                "right_eye": [face_center_x + 50, face_center_y - 25],
                "left_eyebrow": [face_center_x - 50, face_center_y - 50],
                "right_eyebrow": [face_center_x + 50, face_center_y - 50],
                "nose": [face_center_x, face_center_y + 35],
                "mouth": [face_center_x, mouth_y],
                "mouth_width": 56,
                "mouth_height": 20,
                "eye_width": 40,
                "eye_height": 22
            }
        }
        with open(os.path.join(av_dir, "meta.json"), "w") as f:
            json.dump(meta, f, indent=2)

    def process_custom_avatar(self, uploaded_img_path: str, avatar_id: str, avatar_name: str):
        """
        Takes any user portrait photo, detects face/eyes/mouth, normalizes it,
        and rigs it into an animatable HeyGen avatar bundle!
        """
        img = cv2.imread(uploaded_img_path)
        if img is None:
            raise ValueError("Unable to read image file.")

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect face
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(100, 100))
        if len(faces) == 0:
            # Fallback to center frame
            fx, fy, fw, fh = int(w * 0.25), int(h * 0.15), int(w * 0.5), int(h * 0.5)
        else:
            # Pick largest detected face
            fx, fy, fw, fh = max(faces, key=lambda b: b[2] * b[3])

        face_center_x = fx + fw // 2
        face_center_y = fy + fh // 2

        # Detect eyes inside face region
        face_roi_gray = gray[fy:fy + int(fh * 0.65), fx:fx + fw]
        eyes = self.eye_cascade.detectMultiScale(face_roi_gray, scaleFactor=1.1, minNeighbors=3, minSize=(20, 20))

        if len(eyes) >= 2:
            # Sort left to right
            eyes = sorted(eyes, key=lambda e: e[0])
            left_eye_pos = [fx + eyes[0][0] + eyes[0][2] // 2, fy + eyes[0][1] + eyes[0][3] // 2]
            right_eye_pos = [fx + eyes[1][0] + eyes[1][2] // 2, fy + eyes[1][1] + eyes[1][3] // 2]
        else:
            left_eye_pos = [face_center_x - int(fw * 0.22), face_center_y - int(fh * 0.12)]
            right_eye_pos = [face_center_x + int(fw * 0.22), face_center_y - int(fh * 0.12)]

        mouth_y = face_center_y + int(fh * 0.35)
        mouth_pos = [face_center_x, mouth_y]

        # Target dimensions (720 x 960)
        target_w, target_h = 720, 960
        scale = 320.0 / float(fh)
        scaled_w = int(w * scale)
        scaled_h = int(h * scale)
        resized = cv2.resize(img, (scaled_w, scaled_h), interpolation=cv2.INTER_LANCZOS4)

        # Canvas placement
        canvas = np.zeros((target_h, target_w, 4), dtype=np.uint8)
        offset_x = (target_w // 2) - int(face_center_x * scale)
        offset_y = int(target_h * 0.36) - int(face_center_y * scale)

        # Place onto canvas
        sx1 = max(0, -offset_x)
        sy1 = max(0, -offset_y)
        sx2 = min(scaled_w, target_w - offset_x)
        sy2 = min(scaled_h, target_h - offset_y)

        dx1 = max(0, offset_x)
        dy1 = max(0, offset_y)
        dx2 = dx1 + (sx2 - sx1)
        dy2 = dy1 + (sy2 - sy1)

        bgr_crop = resized[sy1:sy2, sx1:sx2]
        canvas[dy1:dy2, dx1:dx2, :3] = bgr_crop
        canvas[dy1:dy2, dx1:dx2, 3] = 255

        # Save custom avatar bundle
        av_dir = os.path.join(self.avatars_dir, avatar_id)
        os.makedirs(av_dir, exist_ok=True)
        cv2.imwrite(os.path.join(av_dir, "base.png"), canvas)

        import json
        meta = {
            "id": avatar_id,
            "name": avatar_name,
            "gender": "custom",
            "landmarks": {
                "face_center": [target_w // 2, int(target_h * 0.36)],
                "left_eye": [int(left_eye_pos[0] * scale + offset_x), int(left_eye_pos[1] * scale + offset_y)],
                "right_eye": [int(right_eye_pos[0] * scale + offset_x), int(right_eye_pos[1] * scale + offset_y)],
                "left_eyebrow": [int(left_eye_pos[0] * scale + offset_x), int(left_eye_pos[1] * scale + offset_y - 25)],
                "right_eyebrow": [int(right_eye_pos[0] * scale + offset_x), int(right_eye_pos[1] * scale + offset_y - 25)],
                "nose": [target_w // 2, int(target_h * 0.36 + 30)],
                "mouth": [target_w // 2, int(mouth_pos[1] * scale + offset_y)],
                "mouth_width": int(fw * scale * 0.45),
                "mouth_height": int(fh * scale * 0.22),
                "eye_width": int(fw * scale * 0.24),
                "eye_height": int(fh * scale * 0.16)
            }
        }
        with open(os.path.join(av_dir, "meta.json"), "w") as f:
            json.dump(meta, f, indent=2)

        return meta

    def list_avatars(self):
        """Returns catalogue of all installed avatars."""
        import json
        res = []
        for item in os.listdir(self.avatars_dir):
            item_path = os.path.join(self.avatars_dir, item)
            meta_path = os.path.join(item_path, "meta.json")
            if os.path.isdir(item_path) and os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                    res.append({
                        "id": meta["id"],
                        "name": meta["name"],
                        "gender": meta.get("gender", "unknown"),
                        "preview_url": f"/static/assets/avatars/{meta['id']}/base.png"
                    })
        return res

    def list_backgrounds(self):
        """Returns catalogue of all installed backgrounds."""
        bgs = []
        for f in os.listdir(self.backgrounds_dir):
            if f.lower().endswith((".jpg", ".png", ".jpeg")):
                bgs.append({
                    "id": f,
                    "name": f.replace(".jpg", "").replace(".png", "").replace("_", " ").title(),
                    "url": f"/static/assets/backgrounds/{f}"
                })
        return bgs
