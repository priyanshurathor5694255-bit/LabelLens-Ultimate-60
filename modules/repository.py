
import json, hashlib, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
DB=ROOT/"data"/"products.json"
AUDIT=ROOT/"data"/"audit.json"

def read(path):
    if not path.exists(): return []
    try:return json.loads(path.read_text())
    except:return []

def product_key(text):
    return hashlib.sha256((text or "").strip().lower().encode()).hexdigest()[:16]

def upsert_product(name, fields, category, score):
    items=read(DB); key=product_key(name)
    found=next((x for x in items if x["key"]==key),None)
    rec={"key":key,"name":name or "Unknown","category":category,"score":score,
         "fields":fields,"updated":time.strftime("%Y-%m-%d %H:%M:%S")}
    if found: found.update(rec)
    else: items.append(rec)
    DB.write_text(json.dumps(items,indent=2))
    return rec

def find_duplicate(name):
    key=product_key(name); return next((x for x in read(DB) if x["key"]==key),None)

def add_audit(action, actor="Demo Inspector", details=None):
    a=read(AUDIT); a.insert(0,{"time":time.strftime("%Y-%m-%d %H:%M:%S"),
      "actor":actor,"action":action,"details":details or {}})
    AUDIT.write_text(json.dumps(a[:2000],indent=2))
    return a[0]
