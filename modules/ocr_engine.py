
import re
import numpy as np
try:
    import easyocr
except Exception:
    easyocr=None

_READER=None
def get_reader():
    global _READER
    if _READER is None and easyocr is not None:
        _READER=easyocr.Reader(["en"],gpu=False)
    return _READER

def run_ocr(image):
    reader=get_reader()
    if reader is None:return [],"EasyOCR could not be imported."
    result=reader.readtext(np.array(image.convert("RGB")))
    return [{"text":str(t),"confidence":float(c),"box":b} for b,t,c in result],None

def normalize_text(text):
    t=text.lower().replace("m.r.p.","mrp").replace("m.r.p","mrp")
    t=re.sub(r"[^a-z0-9₹%./:+\- ]+"," ",t)
    return re.sub(r"\s+"," ",t).strip()

SYNONYMS={
 "manufacturer":["manufactured by","manufacturer","mfd by","mfd. by","made by","manufactured & packed by"],
 "packer":["packed by","packer","pkd by","pkd. by"],
 "net_quantity":["net quantity","net qty","net weight","net wt","contents"],
 "mrp":["mrp","maximum retail price","max retail price","retail price"],
 "batch":["batch no","batch number","batch","lot no","lot number","lot"],
 "date":["mfg date","manufacturing date","manufactured on","mfd date","packed on","pkd on","best before","use by","expiry","exp date"],
 "consumer_care":["consumer care","customer care","care number","helpline","toll free","email us"],
 "origin":["country of origin","made in","origin"]
}

def find_value(full, term, field):
    pattern=re.compile(re.escape(term)+r"\s*[:\-]?\s*([^\n|]{1,100})",re.I)
    m=pattern.search(full)
    if m:return m.group(1).strip()
    return ""

def extract_fields(items):
    text=" ".join(x["text"] for x in items)
    nt=normalize_text(text)
    fields={}
    for field,terms in SYNONYMS.items():
        hit=next((term for term in terms if normalize_text(term) in nt),None)
        fields[field]={"found":bool(hit),"matched_term":hit,"value":find_value(text,hit,field) if hit else ""}
    first=next((x["text"] for x in items if x["confidence"]>=.45 and len(x["text"])>2),"")
    fields["product_name"]={"found":bool(first),"matched_term":"detected title","value":first}
    return fields,text

def terminology_report(text):
    nt=normalize_text(text); found=[]
    for canonical,terms in SYNONYMS.items():
        hits=[x for x in terms if normalize_text(x) in nt]
        if hits: found.append({"canonical":canonical,"detected":hits})
    return found
