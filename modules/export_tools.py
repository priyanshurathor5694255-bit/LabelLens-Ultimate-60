
from pathlib import Path
import pandas as pd, io, time
def csv_bytes(rows): return pd.DataFrame(rows).to_csv(index=False).encode()
def xlsx_bytes(rows):
    b=io.BytesIO()
    with pd.ExcelWriter(b,engine="openpyxl") as w: pd.DataFrame(rows).to_excel(w,index=False,sheet_name="Inspection")
    return b.getvalue()
