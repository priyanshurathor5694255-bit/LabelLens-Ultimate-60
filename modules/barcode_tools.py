def decode_barcodes(image):
    try:
        from pyzbar.pyzbar import decode
        result = decode(image)
        return [{"type": x.type, "data": x.data.decode("utf-8", errors="ignore")} for x in result]
    except Exception:
        return []
