
import io, math
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import numpy as np

def perspective_correct(image):
    # Safe prototype fallback: EXIF orientation + mild sharpening.
    return ImageEnhance.Sharpness(ImageOps.exif_transpose(image).convert("RGB")).enhance(1.2)

def glare_score(image):
    a=np.asarray(image.convert("L"),dtype=np.float32)
    return float(np.mean(a>247))

def blur_score(image):
    try:
        import cv2
        a=np.asarray(image.convert("L"))
        return float(cv2.Laplacian(a,cv2.CV_64F).var())
    except Exception:
        return float(np.asarray(image.convert("L"),dtype=np.float32).var())

def image_diagnostics(image):
    b=blur_score(image); g=glare_score(image)
    return {"blur_score":round(b,2),"glare_ratio":round(g,4),
            "blur_ok":b>=80,"glare_ok":g<0.20}

def detect_products(image, model_path="models/product_detector.pt", conf=0.25):
    # Uses a trained YOLO model when supplied. Otherwise returns a single-image fallback.
    try:
        from ultralytics import YOLO
        import os
        if not os.path.exists(model_path):
            return [{"box":(0,0,image.width,image.height),"confidence":1.0,"class":"package","fallback":True}]
        model=YOLO(model_path)
        res=model.predict(np.asarray(image),conf=conf,verbose=False)[0]
        out=[]
        if res.boxes is not None:
            for b,c in zip(res.boxes.xyxy.tolist(),res.boxes.conf.tolist()):
                x1,y1,x2,y2=map(int,b)
                out.append({"box":(x1,y1,x2,y2),"confidence":float(c),"class":"package","fallback":False})
        return out
    except Exception:
        return [{"box":(0,0,image.width,image.height),"confidence":1.0,"class":"package","fallback":True}]

def crop_products(image, detections):
    crops=[]
    for i,d in enumerate(detections,1):
        x1,y1,x2,y2=d["box"]
        x1=max(0,x1);y1=max(0,y1);x2=min(image.width,x2);y2=min(image.height,y2)
        if x2>x1 and y2>y1:
            crops.append((i,image.crop((x1,y1,x2,y2)),d))
    return crops

def font_size_estimate_mm(image, ocr_items, reference_mm=None):
    # If physical reference/calibration is known, estimate character height in mm.
    # Without calibration, return pixels and INDETERMINATE rather than inventing mm.
    vals=[]
    for item in ocr_items:
        pts=item["box"]; ys=[p[1] for p in pts]
        vals.append(abs(max(ys)-min(ys)))
    px=float(np.median(vals)) if vals else 0
    if reference_mm:
        return {"status":"ESTIMATED","pixel_height":round(px,2),"mm_height":round(px*reference_mm,3)}
    return {"status":"INDETERMINATE","pixel_height":round(px,2),"mm_height":None}

def annotate_products(image,detections):
    from PIL import ImageDraw
    im=image.copy().convert("RGB"); d=ImageDraw.Draw(im)
    for i,x in enumerate(detections,1):
        b=x["box"]; d.rectangle(b,outline=(20,120,180),width=4)
        d.text((b[0]+5,b[1]+5),f"Product {i} • {x['confidence']:.0%}",fill=(20,20,20))
    return im
