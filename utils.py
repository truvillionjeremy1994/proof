import cv2
import numpy as np
from PIL import Image
import piexif


def compute_depth_score(image):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    dx = cv2.Sobel(gray, cv2.CV_64F, 1, 0)
    dy = cv2.Sobel(gray, cv2.CV_64F, 0, 1)
    edge_magnitude = np.hypot(dx, dy)
    score = np.mean(edge_magnitude)
    return score


def compute_lighting_score(image):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    mean_brightness = np.mean(gray)
    return mean_brightness


def compute_texture_score(image):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    score = laplacian.var()
    return score


def compute_metadata_score(image_path):
    try:
        exif_dict = piexif.load(image_path)
        if exif_dict.get("0th") or exif_dict.get("Exif"):
            return 100
        else:
            return 0
    except Exception:
        return 0


def generate_notes(depth, lighting, texture, metadata):
    if metadata == 0:
        return "No EXIF — likely screenshot or repost"
    if depth < 20:
        return "Flat depth — image may be displayed or recycled"
    if texture < 10:
        return "Low texture — possibly compressed, AI-generated or spoofed"
    if lighting > 240 or lighting < 20:
        return "Lighting extreme — may impact authenticity check"
    return "No obvious issues detected"