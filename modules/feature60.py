import io, json, math, re, hashlib, zipfile, time
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw
import numpy as np

ROOT=Path(__file__).resolve().parent.parent
EVIDENCE=ROOT/'data'/'evidence'; EVIDENCE.mkdir(parents=True,exist_ok=True)

# 41. Camera capture is provided by Streamlit camera_input in app.py.
def normalize_visual(image):
    """42. Local color/illumination normalization."""
    img=ImageOps.exif_transpose(image).convert('RGB')
    a=np.asarray(img,dtype=np.float32)
    mean=a.mean(axis=(0,1),keepdims=True)
    scale=128.0/np.maximum(mean,1)
    a=np.clip(a*scale,0,255).astype(np.uint8)
    return Image.fromarray(a)

def denoise(image):
    """43. Conservative local denoise."""
    return image.convert('RGB').filter(ImageFilter.MedianFilter(size=3))

def adaptive_threshold(image):
    """44. Adaptive threshold preview for difficult labels."""
    import cv2
    a=np.asarray(image.convert('L'))
    th=cv2.adaptiveThreshold(a,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,31,11)
    return Image.fromarray(th).convert('RGB')

def deskew(image):
    """45. Text-angle correction using dominant foreground pixels."""
    import cv2
    a=np.asarray(image.convert('L'))
    bw=cv2.threshold(a,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)[1]
    ys,xs=np.where(bw>0)
    if len(xs)<50: return image
    pts=np.column_stack([xs,ys]).astype(np.float32)
    angle=cv2.minAreaRect(pts)[-1]
    if angle < -45: angle=90+angle
    if abs(angle)>10: angle=0
    h,w=a.shape; M=cv2.getRotationMatrix2D((w/2,h/2),angle,1)
    out=cv2.warpAffine(np.asarray(image.convert('RGB')),M,(w,h),borderMode=cv2.BORDER_REPLICATE)
    return Image.fromarray(out)

def perspective_correct_auto(image):
    """46. Automatic quadrilateral perspective correction when a strong label boundary is found."""
    import cv2
    a=np.asarray(image.convert('RGB')); gray=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY)
    edge=cv2.Canny(gray,60,160)
    contours,_=cv2.findContours(edge,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    h,w=gray.shape; best=None; area0=0
    for c in contours:
        area=cv2.contourArea(c)
        if area < 0.20*w*h: continue
        peri=cv2.arcLength(c,True); approx=cv2.approxPolyDP(c,0.02*peri,True)
        if len(approx)==4 and area>area0:
            best=approx.reshape(4,2).astype(np.float32); area0=area
    if best is None: return image.convert('RGB'), False
    s=best.sum(axis=1); d=np.diff(best,axis=1).ravel()
    tl=best[np.argmin(s)]; br=best[np.argmax(s)]; tr=best[np.argmin(d)]; bl=best[np.argmax(d)]
    dst=np.array([[0,0],[w-1,0],[w-1,h-1],[0,h-1]],np.float32)
    src=np.array([tl,tr,br,bl],np.float32)
    M=cv2.getPerspectiveTransform(src,dst)
    out=cv2.warpPerspective(a,M,(w,h))
    return Image.fromarray(out), True

def detect_regions(image):
    """47. Local package/label region proposal. This is deterministic CV, not a trained detector."""
    import cv2
    a=np.asarray(image.convert('RGB')); gray=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY)
    blur=cv2.GaussianBlur(gray,(5,5),0); edge=cv2.Canny(blur,50,150)
    contours,_=cv2.findContours(edge,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    h,w=gray.shape; boxes=[]
    for c in contours:
        x,y,ww,hh=cv2.boundingRect(c); ar=ww/max(hh,1); area=ww*hh/(w*h)
        if area>=0.04 and 0.25<=ar<=4.5:
            boxes.append((x,y,x+ww,y+hh))
    # non-max suppression
    boxes=sorted(boxes,key=lambda b:(b[2]-b[0])*(b[3]-b[1]),reverse=True)
    keep=[]
    for b in boxes:
        x1,y1,x2,y2=b
        ok=True
        for q in keep:
            xa,ya,xb,yb=q; ix=max(0,min(x2,xb)-max(x1,xa)); iy=max(0,min(y2,yb)-max(y1,ya))
            inter=ix*iy; union=(x2-x1)*(y2-y1)+(xb-xa)*(yb-ya)-inter
            if union and inter/union>0.65: ok=False; break
        if ok: keep.append(b)
    return keep[:100]

def crop_regions(image, boxes):
    return [(i+1,image.crop(b),b) for i,b in enumerate(boxes)]

def qr_codes(image):
    """48. QR detection/decoding using OpenCV, fully local."""
    import cv2
    det=cv2.QRCodeDetector(); a=np.asarray(image.convert('RGB'))
    out=[]
    try:
        ok,info,pts,_=det.detectAndDecodeMulti(a)
        if ok and info is not None:
            for i,s in enumerate(info):
                if s: out.append({'type':'QR','data':s,'index':i})
    except Exception: pass
    try:
        s,pts,_=det.detectAndDecode(a)
        if s and not any(x['data']==s for x in out): out.append({'type':'QR','data':s,'index':0})
    except Exception: pass
    return out

def barcode_codes(image):
    """49. 1-D barcode decoding when optional pyzbar + system zbar are available."""
    try:
        from pyzbar.pyzbar import decode
        return [{'type':x.type,'data':x.data.decode('utf-8','ignore')} for x in decode(image)]
    except Exception as e:
        return []

def text_scale_calibration(pixel_reference, physical_reference_mm):
    """50. Explicit pixels-per-mm calibration."""
    if pixel_reference<=0 or physical_reference_mm<=0: raise ValueError('Reference values must be positive.')
    return {'px_per_mm':pixel_reference/physical_reference_mm,'reference_px':pixel_reference,'reference_mm':physical_reference_mm}

def physical_text_height(pixel_height, calibration):
    """51. Calibrated physical text-height estimate; never invents scale."""
    if not calibration or calibration.get('px_per_mm',0)<=0: return {'status':'INDETERMINATE','mm':None}
    return {'status':'ESTIMATED','mm':round(pixel_height/calibration['px_per_mm'],3)}

def multilingual_reader(languages):
    """52. Configurable EasyOCR language pack (English/Hindi/other supported codes)."""
    import easyocr
    langs=[]
    for x in languages:
        x=x.strip().lower()
        if x and x not in langs: langs.append(x)
    if not langs: langs=['en']
    return easyocr.Reader(langs,gpu=False)

def field_confidence(fields, ocr_items):
    """53. Evidence confidence aggregation per extracted field."""
    confs=[float(x.get('confidence',0)) for x in ocr_items]
    base=float(np.mean(confs)) if confs else 0
    out={}
    for k,v in fields.items():
        out[k]=round(base if v.get('found') else min(base,0.25),3)
    return out

def corrections(rows):
    """54. Actionable correction suggestions."""
    out=[]
    for r in rows:
        s=r.get('Status','')
        if s=='PASS': action='No action required from this check.'
        elif 'font' in r.get('Field','').lower(): action='Retake a straight, calibrated image and verify print height manually.'
        elif 'image' in r.get('Field','').lower(): action='Retake with even lighting, less glare and sharper focus.'
        else: action=f"Verify the declaration for {r.get('Field','').lower()} and correct the label if applicable."
        out.append({**r,'Suggested action':action})
    return out

def rule_pack_manifest():
    """55. Versioned rule-pack manifest."""
    p=ROOT/'data'/'rules_full.json'
    try: meta=json.loads(p.read_text()).get('meta',{})
    except Exception: meta={}
    return {'name':meta.get('name','LabelLens rule pack'),'version':meta.get('version','unknown'),'checked_at':time.strftime('%Y-%m-%d %H:%M:%S'),'mode':'prototype / validate against current official rules'}

def image_fingerprint(image):
    """56. SHA-256 evidence fingerprint."""
    buf=io.BytesIO(); image.convert('RGB').save(buf,format='PNG')
    return hashlib.sha256(buf.getvalue()).hexdigest()

def save_evidence(scan_id, image, metadata):
    """57. Local evidence vault."""
    folder=EVIDENCE/scan_id; folder.mkdir(exist_ok=True)
    image_path=folder/'primary.png'; image.convert('RGB').save(image_path)
    meta=dict(metadata); meta['fingerprint']=image_fingerprint(image); meta['saved_at']=time.strftime('%Y-%m-%d %H:%M:%S')
    (folder/'metadata.json').write_text(json.dumps(meta,indent=2,default=str),encoding='utf-8')
    return folder

def evidence_bundle(scan_id):
    """58. Portable ZIP evidence bundle."""
    folder=EVIDENCE/scan_id
    if not folder.exists(): return None
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob('*'):
            if p.is_file(): z.write(p,p.relative_to(folder))
    return buf.getvalue()

def compare_scans(previous_score, current_score):
    """59. Repeat-inspection delta intelligence."""
    if previous_score is None: return {'delta':None,'direction':'FIRST INSPECTION'}
    d=round(current_score-previous_score,2)
    return {'delta':d,'direction':'IMPROVED' if d>0 else 'DECLINED' if d<0 else 'UNCHANGED'}

def reviewer_note(scan_id, note, reviewer='Human reviewer'):
    """60. Human-review annotation stored locally."""
    p=ROOT/'data'/'review_notes.json'
    try: arr=json.loads(p.read_text())
    except Exception: arr=[]
    arr.insert(0,{'scan_id':scan_id,'reviewer':reviewer,'note':note,'time':time.strftime('%Y-%m-%d %H:%M:%S')})
    p.write_text(json.dumps(arr[:2000],indent=2),encoding='utf-8')
    return arr[0]
