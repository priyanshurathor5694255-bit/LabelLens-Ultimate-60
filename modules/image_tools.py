from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np

def prepare_image(image):
    img = image.convert("RGB")
    img = ImageOps.exif_transpose(img)
    max_side = 1800
    if max(img.size) > max_side:
        ratio = max_side / max(img.size)
        img = img.resize((int(img.width*ratio), int(img.height*ratio)))
    img = ImageEnhance.Contrast(img).enhance(1.12)
    img = ImageEnhance.Sharpness(img).enhance(1.15)
    return img

def quality_check(image):
    arr = np.asarray(image.convert("L"))
    variance = float(arr.var())
    mean = float(arr.mean())
    issues = []
    if min(image.size) < 500:
        issues.append("Low resolution")
    if variance < 120:
        issues.append("Low contrast / possible blur")
    if mean > 245 or mean < 15:
        issues.append("Extreme brightness")
    return {"ok": not issues, "issues": issues, "width": image.width, "height": image.height}

def annotate_image(image, ocr_items, bad_terms=None):
    from PIL import ImageDraw, ImageFont
    img = image.copy().convert("RGB")
    draw = ImageDraw.Draw(img)
    bad_terms = bad_terms or []
    for item in ocr_items:
        box = item["box"]
        pts = [(int(p[0]), int(p[1])) for p in box]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        xy = (min(xs), min(ys), max(xs), max(ys))
        txt = item["text"]
        is_bad = any(t.lower() in txt.lower() for t in bad_terms)
        draw.rectangle(xy, outline=(210,40,40) if is_bad else (20,150,90), width=3)
        draw.text((xy[0], max(0, xy[1]-18)), txt[:35], fill=(20,20,20))
    return img
