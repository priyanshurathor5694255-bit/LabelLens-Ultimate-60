
import json,time,hashlib
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/"data"; DATA.mkdir(exist_ok=True)
HISTORY=DATA/"history.json"; PRODUCTS=DATA/"products.json"; AUDIT=DATA/"audit.json"

def read(p):
    if not p.exists(): return []
    try:return json.loads(p.read_text())
    except:return []

def write(p,x): p.write_text(json.dumps(x,indent=2),encoding="utf-8")

def load_history(): return read(HISTORY)
def history_df(): return pd.DataFrame(load_history())

def save_scan(product,category,stats,status):
    h=load_history()
    rec={"scan_id":f"LL-{int(time.time()*1000)}","timestamp":time.strftime("%Y-%m-%d %H:%M:%S"),
         "product":product or "Unknown","category":category,"score":stats["score"],"status":status}
    h.insert(0,rec); write(HISTORY,h[:1000]); add_audit("scan_created",rec); return rec

def key(name): return hashlib.sha256((name or "unknown").strip().lower().encode()).hexdigest()[:16]
def find_product(name):
    k=key(name); return next((x for x in read(PRODUCTS) if x["key"]==k),None)
def upsert_product(name,category,score,fields):
    p=read(PRODUCTS); k=key(name); old=find_product(name)
    rec={"key":k,"product":name or "Unknown","category":category,"score":score,"fields":fields,"updated":time.strftime("%Y-%m-%d %H:%M:%S")}
    if old: old.update(rec)
    else:p.append(rec)
    write(PRODUCTS,p); return rec
def add_audit(action,details=None,actor="Demo Inspector"):
    a=read(AUDIT); a.insert(0,{"time":time.strftime("%Y-%m-%d %H:%M:%S"),"actor":actor,"action":action,"details":details or {}}); write(AUDIT,a[:2000])
def audit_df(): return pd.DataFrame(read(AUDIT))
def product_df(): return pd.DataFrame(read(PRODUCTS))
