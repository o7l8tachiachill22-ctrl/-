"""
Atmospheric video generator - creates a cinematic, moody animation from a still image.
Effects: subtle Ken Burns zoom, lamp flicker, bokeh particles, vignette pulse, color grading.
"""

import cv2
import numpy as np
from PIL import Image
import math
import random

INPUT_IMAGE = "/root/.claude/uploads/adce64ab-16d8-4651-a1ae-4d3404e6a48b/019dbf8e-1000016008.png"
OUTPUT_VIDEO = "/home/user/-/atmospheric_output.mp4"
FPS = 30
DURATION_SEC = 10
TOTAL_FRAMES = FPS * DURATION_SEC


def load_image(path):
    img = Image.open(path).convert("RGB")
    img = img.resize((960, 540), Image.LANCZOS)
    return np.array(img)


def apply_color_grade(frame):
    """Warm cinematic color grade: lift shadows, add golden tones."""
    f = frame.astype(np.float32) / 255.0
    # Warm highlights
    f[:, :, 0] = np.clip(f[:, :, 0] * 1.05 + 0.02, 0, 1)   # R up
    f[:, :, 2] = np.clip(f[:, :, 2] * 0.92, 0, 1)           # B down
    # Slight lift in shadows (cinematic S-curve)
    f = np.clip(f * 0.95 + 0.03, 0, 1)
    return (f * 255).astype(np.uint8)


def apply_vignette(frame, strength):
    """Pulsing vignette."""
    h, w = frame.shape[:2]
    Y, X = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    dist = np.sqrt(((X - cx) / (w * 0.6)) ** 2 + ((Y - cy) / (h * 0.6)) ** 2)
    mask = np.clip(1.0 - dist * strength, 0, 1)
    mask = mask[:, :, np.newaxis]
    return (frame.astype(np.float32) * mask).astype(np.uint8)


def ken_burns(base, t):
    """Slow zoom-in Ken Burns effect."""
    h, w = base.shape[:2]
    scale = 1.0 + 0.06 * t          # zoom from 1.0x to 1.06x
    new_w = int(w / scale)
    new_h = int(h / scale)
    x0 = (w - new_w) // 2
    y0 = (h - new_h) // 2
    cropped = base[y0:y0 + new_h, x0:x0 + new_w]
    return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)


def lamp_flicker(frame, t, lamp_x, lamp_y, radius=80):
    """Simulate warm lamp light flickering."""
    flicker = 0.85 + 0.15 * (
        0.5 * math.sin(t * 13.7) +
        0.3 * math.sin(t * 31.1) +
        0.2 * math.sin(t * 7.3)
    )
    h, w = frame.shape[:2]
    Y, X = np.ogrid[:h, :w]
    dist = np.sqrt((X - lamp_x) ** 2 + (Y - lamp_y) ** 2)
    glow = np.clip(1.0 - dist / radius, 0, 1) ** 1.5 * flicker * 0.35
    result = frame.astype(np.float32)
    result[:, :, 0] = np.clip(result[:, :, 0] + glow * 80, 0, 255)   # R
    result[:, :, 1] = np.clip(result[:, :, 1] + glow * 45, 0, 255)   # G
    result[:, :, 2] = np.clip(result[:, :, 2] + glow * 10, 0, 255)   # B
    return result.astype(np.uint8)


class Particle:
    def __init__(self, w, h):
        self.reset(w, h, init=True)

    def reset(self, w, h, init=False):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h) if init else h + 5
        self.size = random.uniform(1.5, 4.5)
        self.speed = random.uniform(0.15, 0.6)
        self.alpha = random.uniform(0.05, 0.25)
        self.drift = random.uniform(-0.3, 0.3)
        self.w = w
        self.h = h

    def update(self):
        self.y -= self.speed
        self.x += self.drift
        if self.y < -10:
            self.reset(self.w, self.h)

    def draw(self, canvas):
        xi, yi = int(self.x), int(self.y)
        h, w = canvas.shape[:2]
        if 0 <= xi < w and 0 <= yi < h:
            cv2.circle(canvas, (xi, yi), int(self.size), (220, 200, 170), -1)


def draw_particles(frame, particles):
    overlay = np.zeros_like(frame, dtype=np.uint8)
    for p in particles:
        p.draw(overlay)
    mask = (overlay.sum(axis=2) > 0).astype(np.float32)[:, :, np.newaxis]
    alpha_map = mask * 0.18
    result = frame.astype(np.float32) * (1 - alpha_map) + overlay.astype(np.float32) * alpha_map
    return result.astype(np.uint8)


def ease_inout(t):
    return t * t * (3 - 2 * t)


def main():
    base = load_image(INPUT_IMAGE)
    h, w = base.shape[:2]

    # Lamp position (right side, upper area – matching scene)
    lamp_x = int(w * 0.78)
    lamp_y = int(h * 0.38)

    # Pre-apply color grade to base
    base = apply_color_grade(base)

    # Initialize particles
    particles = [Particle(w, h) for _ in range(55)]

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, FPS, (w, h))

    for i in range(TOTAL_FRAMES):
        t = i / TOTAL_FRAMES          # 0.0 → 1.0
        t_sec = i / FPS

        # Ken Burns
        frame = ken_burns(base, ease_inout(t))

        # Lamp flicker
        frame = lamp_flicker(frame, t_sec, lamp_x, lamp_y)

        # Vignette pulse (subtle breathing)
        vignette_strength = 1.05 + 0.08 * math.sin(t_sec * 0.8)
        frame = apply_vignette(frame, vignette_strength)

        # Dust/bokeh particles
        for p in particles:
            p.update()
        frame = draw_particles(frame, particles)

        # Fade in / fade out
        if i < FPS:
            alpha = i / FPS
            frame = (frame.astype(np.float32) * alpha).astype(np.uint8)
        elif i > TOTAL_FRAMES - FPS:
            alpha = (TOTAL_FRAMES - i) / FPS
            frame = (frame.astype(np.float32) * alpha).astype(np.uint8)

        # OpenCV uses BGR
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)

        if i % (FPS * 2) == 0:
            print(f"  {i // FPS}s / {DURATION_SEC}s done...")

    out.release()
    print(f"\nDone! Saved to: {OUTPUT_VIDEO}")


if __name__ == "__main__":
    main()
