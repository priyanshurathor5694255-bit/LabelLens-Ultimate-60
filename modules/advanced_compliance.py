
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
RULES=ROOT/"data"/"rules_full.json"

def load_full_rules():
    try:return json.loads(RULES.read_text())
    except Exception:return {"rules":[]}

def evaluate_full(fields, category="food", diagnostics=None, font=None):
    rules=load_full_rules()["rules"]; rows=[]
    for r in rules:
        f=fields.get(r["field"],{})
        if f.get("found"):
            status="PASS"; evidence=f"Detected term: {f.get('matched_term','')}"
        elif r["required"]:
            status="POTENTIAL NON-COMPLIANCE"; evidence="Required field not detected in submitted evidence."
        else:
            status="REVIEW"; evidence="Applicability/evidence should be verified."
        rows.append({"Rule ID":r["id"],"Field":r["label"],"Status":status,
                     "Evidence":evidence,"Rule source":r["source"]})
    if diagnostics:
        if not diagnostics.get("blur_ok",True) or not diagnostics.get("glare_ok",True):
            rows.append({"Rule ID":"IMG-001","Field":"Image evidence quality","Status":"REVIEW",
                         "Evidence":f"Blur={diagnostics.get('blur_score')}; glare={diagnostics.get('glare_ratio')}",
                         "Rule source":"Evidence quality gate"})
    if font and font.get("status")=="INDETERMINATE":
        rows.append({"Rule ID":"VIS-001","Field":"Font-size verification","Status":"REVIEW",
                     "Evidence":f"Observed median text height {font.get('pixel_height')} px; physical calibration unavailable.",
                     "Rule source":"Visual measurement"})
    return rows

def corrective_suggestion(row):
    s=row["Status"]
    if s=="PASS": return "No corrective action suggested."
    if row["Field"].lower().startswith("font"): return "Capture a calibrated, straight-on image or verify physical print size manually."
    return f"Verify the {row['Field'].lower()} declaration and correct the label if required."

def evidence_record(scan_id, row, image_region=None):
    return {"scan_id":scan_id,"rule_id":row["Rule ID"],"field":row["Field"],
            "status":row["Status"],"evidence":row["Evidence"],"region":image_region}
