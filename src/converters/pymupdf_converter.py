import fitz
import base64

def pdf_to_images(pdf_path: str, dpi: int = 150) -> list[dict]:
    doc = fitz.open(pdf_path)
    base64_images = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=matrix)
        img_bytes = pix.tobytes("png")
        base64_images.append({
            "page": i + 1,
            "base64": base64.b64encode(img_bytes).decode("utf-8"),
        })
    doc.close()
    return base64_images