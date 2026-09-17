
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def rules():
    p=ROOT/"data"/"rules_full.json"
    if p.exists(): return json.loads(p.read_text()).get("rules",[])
    return []
def evaluate(fields, diagnostics=None, font=None):
    rows=[]
    for r in rules():
        f=fields.get(r["field"],{})
        if f.get("found"): status="PASS"; evidence=f"Detected: {f.get('matched_term')}"
        elif r.get("required"): status="POTENTIAL NON-COMPLIANCE"; evidence="Required field not detected."
        else: status="REVIEW"; evidence="Optional/applicability needs review."
        rows.append({"Rule ID":r["id"],"Field":r["label"],"Status":status,"Evidence":evidence,"Source":r["source"]})
    if diagnostics and not all([diagnostics["resolution_ok"],diagnostics["sharpness_ok"],diagnostics["glare_ok"],diagnostics["dark_ok"]]):
        rows.append({"Rule ID":"IMG-001","Field":"Image quality","Status":"REVIEW","Evidence":"Image quality may reduce confidence.","Source":"Local image-quality gate"})
    if font and font["sample_count"]==0:
        rows.append({"Rule ID":"VIS-001","Field":"Text measurement","Status":"REVIEW","Evidence":"No measurable OCR text region.","Source":"Local visual measurement"})
    return rows
def stats(rows):
    p=sum(r["Status"]=="PASS" for r in rows); i=sum(r["Status"]=="POTENTIAL NON-COMPLIANCE" for r in rows); q=sum(r["Status"]=="REVIEW" for r in rows)
    return {"total":len(rows),"passed":p,"issues":i,"review":q,"score":round(100*p/len(rows),1) if rows else 0}
