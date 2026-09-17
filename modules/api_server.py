
# Optional FastAPI adapter. Install fastapi + uvicorn separately if you want to expose an API.
def analyze_payload(payload):
    """Contract for future external integrations."""
    return {"status":"accepted","message":"Connect this adapter to the same OCR/compliance pipeline used by Streamlit."}
