
import pandas as pd
def summary(df):
    if df is None or df.empty:return {}
    return {
      "total":len(df),
      "pass":int((df["status"]=="PASS").sum()),
      "review":int((df["status"]=="REVIEW").sum()),
      "issues":int((df["status"]=="POTENTIAL NON-COMPLIANCE").sum()),
      "avg_score":round(float(df["score"].mean()),1) if "score" in df else 0
    }
def category_stats(df):
    if df is None or df.empty or "category" not in df:return pd.DataFrame()
    return df.groupby("category",as_index=False)["score"].mean().rename(columns={"score":"average_score"})
def trend(df):
    if df is None or df.empty:return pd.DataFrame()
    x=df.copy(); x["date"]=pd.to_datetime(x["timestamp"]).dt.date
    return x.groupby("date",as_index=False)["score"].mean()
