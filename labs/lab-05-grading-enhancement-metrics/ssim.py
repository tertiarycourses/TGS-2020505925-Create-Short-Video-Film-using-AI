"""SSIM and PSNR in NumPy + OpenCV.

cv2.quality (which has an SSIM) lives in opencv-contrib-python, not in the base
wheel, so the course ships this small implementation instead of an extra
dependency. It follows Wang et al. (2004): Gaussian window sigma 1.5,
K1 = 0.01, K2 = 0.03, L = 255, computed on the luma channel.
"""
import cv2
import numpy as np


def _luma(img):
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img.astype(np.float64)


def ssim(a, b):
    """Mean structural similarity of two same-size images, in [-1, 1]."""
    if a.shape != b.shape:
        raise ValueError("ssim: images must be the same size")
    x, y = _luma(a), _luma(b)
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    g = lambda z: cv2.GaussianBlur(z, (11, 11), 1.5)
    mx, my = g(x), g(y)
    sxx = g(x * x) - mx * mx
    syy = g(y * y) - my * my
    sxy = g(x * y) - mx * my
    num = (2 * mx * my + c1) * (2 * sxy + c2)
    den = (mx * mx + my * my + c1) * (sxx + syy + c2)
    return float((num / den).mean())


def psnr(a, b):
    """Peak signal-to-noise ratio in dB for 8-bit images (inf when identical)."""
    mse = float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2))
    return float("inf") if mse == 0 else 10.0 * np.log10(255.0 ** 2 / mse)


if __name__ == "__main__":
    z = np.random.default_rng(0).integers(0, 256, (64, 64), dtype=np.uint8)
    assert abs(ssim(z, z) - 1.0) < 1e-9 and psnr(z, z) == float("inf")
    print("ssim self-test passed")
