# LabelLens Ultimate 60 — Mac

This build expands the local-first prototype to **60 implemented feature areas**. It adds a deterministic visual pipeline, camera capture, QR decoding, optional 1-D barcode decoding, multilingual EasyOCR options, explicit physical-scale calibration, evidence fingerprinting/vault/bundles, repeat-inspection deltas and reviewer annotations.

## Run on macOS
```bash
cd LabelLens_Ultimate_60_Perfected
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## What “60 implemented” means
All 60 items in the Features page have runnable code paths. Advanced capabilities are **evidence-gated**:
- Physical font size is INDETERMINATE until a known physical reference is supplied.
- 1-D barcode decoding uses `pyzbar` only when the macOS `zbar` runtime is available; the app continues safely when it is not.
- Package region detection is deterministic computer vision, not a claimed trained product detector.
- Multilingual OCR downloads EasyOCR language models on first use and depends on those models being available.
- External government, e-commerce, cloud authentication and cloud databases are intentionally not fabricated.

## Legal/data note
`data/rules_full.json` is a prototype rule-pack structure. Validate and version every rule against the currently applicable official Indian regulations before enforcement or commercial use.
