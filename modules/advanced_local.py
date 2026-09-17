
from PIL import Image, ImageEnhance, ImageOps, ImageFilter, ImageDraw
import numpy as np, cv2, hashlib, time

def prepare(image):
    image=ImageOps.exif_transpose(image).convert("RGB")
    max_side=1800
    if max(image.size)>max_side:
        r=max_side/max(image.size); image=image.resize((int(image.width*r),int(image.height*r)))
    image=ImageEnhance.Contrast(image).enhance(1.15)
    image=ImageEnhance.Sharpness(image).enhance(1.25)
    return image

def diagnostics(image):
    gray=np.asarray(image.convert("L"))
    lap=float(cv2.Laplacian(gray,cv2.CV_64F).var())
    glare=float((gray>247).mean())
    dark=float((gray<12).mean())
    return {"width":image.width,"height":image.height,"sharpness":round(lap,2),
            "glare_ratio":round(glare,3),"dark_ratio":round(dark,3),
            "resolution_ok":min(image.size)>=500,"sharpness_ok":lap>=80,
            "glare_ok":glare<.20,"dark_ok":dark<.25}

def evidence_overlay(image,items):
    im=image.copy(); d=ImageDraw.Draw(im)
    for i,x in enumerate(items,1):
        pts=[(int(p[0]),int(p[1])) for p in x["box"]]
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        box=(min(xs),min(ys),max(xs),max(ys))
        d.rectangle(box,outline=(18,183,134),width=3)
        d.text((box[0]+4,max(0,box[1]-16)),f"{i} • {x['text'][:28]}",fill=(16,24,40))
    return im

def font_pixels(items):
    heights=[]
    for x in items:
        ys=[p[1] for p in x["box"]]
        if ys: heights.append(abs(max(ys)-min(ys)))
    return {"median_text_height_px":round(float(np.median(heights)),2) if heights else 0,
            "sample_count":len(heights),
            "status":"MEASURED IN PIXELS"}

def image_hash(image):
    import io
    b=io.BytesIO(); image.save(b,format="JPEG",quality=85)
    return hashlib.sha256(b.getvalue()).hexdigest()[:20]

def crop_grid(image, rows=2, cols=2):
    # Useful for batch-style multi-photo sheets; not a physical product detector.
    out=[]
    w,h=image.size
    for r in range(rows):
        for c in range(cols):
            box=(c*w//cols,r*h//rows,(c+1)*w//cols,(r+1)*h//rows)
            out.append(image.crop(box))
    return out
