import cv2
import numpy as np
from pathlib import Path

CASCADES = [
    cv2.CascadeClassifier(
        "/usr/local/lib/python3.11/dist-packages/cv2/data/haarcascade_frontalface_default.xml"
    ),
    cv2.CascadeClassifier(
        "/usr/local/lib/python3.11/dist-packages/cv2/data/haarcascade_frontalface_alt2.xml"
    ),
    cv2.CascadeClassifier(
        "/usr/local/lib/python3.11/dist-packages/cv2/data/haarcascade_frontalface_alt.xml"
    ),
]


def detect_faces_all_rotations(img_gray):
    h, w = img_gray.shape
    min_face = max(int(min(h, w) * 0.06), 30)
    best_faces, best_rot = [], 0

    for rot in [0, 90, 270, 180]:
        if rot == 90:
            rotated = cv2.rotate(img_gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif rot == 180:
            rotated = cv2.rotate(img_gray, cv2.ROTATE_180)
        elif rot == 270:
            rotated = cv2.rotate(img_gray, cv2.ROTATE_90_CLOCKWISE)
        else:
            rotated = img_gray

        for cascade in CASCADES:
            faces = cascade.detectMultiScale(
                rotated,
                scaleFactor=1.08,
                minNeighbors=4,
                minSize=(min_face, min_face),
            )
            if len(faces) > len(best_faces):
                best_faces = faces
                best_rot = rot

    return best_faces, best_rot


def rotate_image(img, rot):
    if rot == 90:
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif rot == 180:
        return cv2.rotate(img, cv2.ROTATE_180)
    elif rot == 270:
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img


def unrotate_image(img, rot):
    if rot == 90:
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif rot == 180:
        return cv2.rotate(img, cv2.ROTATE_180)
    elif rot == 270:
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return img


def anime_filter(img):
    """Stylize image as anime/cartoon."""
    stylized = cv2.stylization(img, sigma_s=60, sigma_r=0.45)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.adaptiveThreshold(
        cv2.medianBlur(gray, 7),
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        blockSize=9,
        C=9,
    )
    edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    anime = cv2.bitwise_and(stylized, edges_bgr)

    hsv = cv2.cvtColor(anime, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.5, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def mosaic(img, block_size=20):
    h, w = img.shape[:2]
    small = cv2.resize(
        img,
        (max(1, w // block_size), max(1, h // block_size)),
        interpolation=cv2.INTER_LINEAR,
    )
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)


def build_person_mask_simple(h, w, faces):
    """Create a soft elliptical mask covering estimated person body from face boxes."""
    mask = np.zeros((h, w), dtype=np.float32)

    for fx, fy, fw, fh in faces:
        cx = fx + fw // 2

        # Estimate person body: width ~2.5x face, height ~7x face
        person_w = int(fw * 2.8)
        person_h = int(fh * 7.5)

        # Center is slightly below the face center
        body_cy = fy + int(fh * 3.5)
        body_cx = cx

        # Draw a filled ellipse for the person region
        person_mask = np.zeros((h, w), dtype=np.float32)
        cv2.ellipse(
            person_mask,
            (body_cx, body_cy),
            (person_w // 2, person_h // 2),
            0,
            0,
            360,
            1.0,
            -1,
        )
        mask = np.maximum(mask, person_mask)

    # Gaussian blur for soft edges
    mask = cv2.GaussianBlur(mask, (61, 61), 0)
    return np.clip(mask, 0, 1)


def process_image(input_path: str, output_path: str):
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read: {input_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces, rot = detect_faces_all_rotations(gray)
    print(f"  Detected {len(faces)} face(s) at rotation={rot}")

    img_rot = rotate_image(img, rot)
    h, w = img_rot.shape[:2]

    bg_mosaic = mosaic(img_rot, block_size=18)

    if len(faces) > 0:
        # Build soft person mask
        person_mask_f = build_person_mask_simple(h, w, faces)
        pm3 = np.stack([person_mask_f] * 3, axis=2)

        # Composite: person original blended over mosaic background
        result = (
            img_rot.astype(np.float32) * pm3 + bg_mosaic.astype(np.float32) * (1 - pm3)
        ).astype(np.uint8)

        # Apply anime filter to each face region
        for x, y, fw, fh in faces:
            pad_x = int(fw * 0.4)
            pad_y = int(fh * 0.5)
            x1 = max(0, x - pad_x)
            y1 = max(0, y - pad_y)
            x2 = min(w, x + fw + pad_x)
            y2 = min(h, y + fh + pad_y)

            face_crop = img_rot[y1:y2, x1:x2]
            anime_face = anime_filter(face_crop)

            rh, rw = y2 - y1, x2 - x1
            em = np.zeros((rh, rw), dtype=np.float32)
            cv2.ellipse(
                em,
                (rw // 2, rh // 2),
                (max(1, rw // 2 - 4), max(1, rh // 2 - 4)),
                0,
                0,
                360,
                1.0,
                -1,
            )
            em = cv2.GaussianBlur(em, (25, 25), 0)
            em3 = np.stack([em] * 3, axis=2)

            region = result[y1:y2, x1:x2].astype(np.float32)
            result[y1:y2, x1:x2] = (
                anime_face.astype(np.float32) * em3 + region * (1 - em3)
            ).astype(np.uint8)
    else:
        print("  No faces found — applying mosaic to full image")
        result = bg_mosaic

    result = unrotate_image(result, rot)
    cv2.imwrite(output_path, result, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"  Saved -> {output_path}")


input_dir = Path("/root/.claude/uploads/7b84a0f7-a2d3-4a18-9813-3c4b13e00955")
output_dir = Path("/home/user/-/output")
output_dir.mkdir(exist_ok=True)

files = [
    "019dc4cc-1000009762.jpg",
    "019dc4cc-1000009760.jpg",
]

for fname in files:
    inp = str(input_dir / fname)
    out = str(output_dir / f"anime_{fname}")
    print(f"Processing: {fname}")
    process_image(inp, out)

print("Done!")
