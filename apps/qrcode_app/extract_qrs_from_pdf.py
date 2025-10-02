import os
import sys
import csv
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional

import fitz            # PyMuPDF
import cv2             # OpenCV
import numpy as np
from PIL import Image

# ===================== CONFIG =====================
BASE_DIR   = Path(__file__).resolve().parent
PDF_PATH   = BASE_DIR / "qrs_pdfs" / "qrs_unificado.pdf"
OUT_DIR    = BASE_DIR / "qrs_extracao"
PNG_DIR    = OUT_DIR / "qrs_png"
CSV_PATH   = OUT_DIR / "mapa_qrs.csv"

RENDER_DPI          = 300   # aumente ou reduza se necessário
FORCE_SQUARE        = True
PADDING_FRACTION    = 0.04  # padding relativo ao maior lado detectado
MIN_SIDE_PIXELS     = 40    # ignora detectados muito pequenos
IGNORE_EMPTY_DECODE = True  # se True, ignorará QRs onde decode veio vazio
# ==================================================

NORMALIZE_ID_REGEX = re.compile(r'([^/\\]+)$')
ID_SANITIZE_REGEX  = re.compile(r'[^A-Za-z0-9._-]')
T_PATTERN          = re.compile(r'\b(T\d{2,})\b')

@dataclass
class QRResult:
    page_number: int
    data: str
    file_name: str
    polygon: List[Tuple[float, float]]
    engine: str

def log(msg: str):
    print(msg, flush=True)

def ensure_dirs():
    PNG_DIR.mkdir(parents=True, exist_ok=True)

def pixmap_to_cv(page_pixmap) -> np.ndarray:
    """Converte fitz.Pixmap para imagem OpenCV (BGR)."""
    if page_pixmap.alpha:
        # Remove alpha canal
        pix = fitz.Pixmap(fitz.csRGB, page_pixmap)
    else:
        pix = page_pixmap
    img = np.frombuffer(pix.samples, dtype=np.uint8)
    img = img.reshape(pix.height, pix.width, 3)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    if page_pixmap.alpha:
        pix = None
    return img

def derive_id_from_data(data: str) -> str:
    if not data:
        return "QR"
    m_t = T_PATTERN.search(data)
    if m_t:
        return m_t.group(1)
    m_last = NORMALIZE_ID_REGEX.search(data.strip())
    candidate = m_last.group(1) if m_last else data.strip()
    candidate = ID_SANITIZE_REGEX.sub("_", candidate)
    if len(candidate) > 32:
        candidate = candidate[:32]
    return candidate or "QR"

def crop_polygon(image: np.ndarray, poly: np.ndarray, padding_frac: float) -> np.ndarray:
    """
    Recorta região do QR com base no polígono retornado pelo detector.
    poly: shape (4,2)
    """
    x_coords = poly[:, 0]
    y_coords = poly[:, 1]
    x_min, x_max = x_coords.min(), x_coords.max()
    y_min, y_max = y_coords.min(), y_coords.max()

    width  = x_max - x_min
    height = y_max - y_min
    side   = max(width, height)

    pad = side * padding_frac
    x_min_p = max(0, int(x_min - pad))
    y_min_p = max(0, int(y_min - pad))
    x_max_p = min(image.shape[1], int(x_min + side + pad))
    y_max_p = min(image.shape[0], int(y_min + side + pad))

    crop = image[y_min_p:y_max_p, x_min_p:x_max_p]

    if FORCE_SQUARE:
        # centraliza corte para quadrado exato se dimensões divergirem
        h, w = crop.shape[:2]
        if w != h:
            side2 = min(w, h)
            x_off = (w - side2) // 2
            y_off = (h - side2) // 2
            crop = crop[y_off:y_off+side2, x_off:x_off+side2]
    return crop

def decode_qrs_on_page(page_image_bgr: np.ndarray, page_number: int) -> List[QRResult]:
    detector = cv2.QRCodeDetector()

    # Multi detecção
    ok, decoded_infos, points, _ = detector.detectAndDecodeMulti(page_image_bgr)
    results: List[QRResult] = []

    if ok and points is not None:
        for info, poly in zip(decoded_infos, points):
            if poly is None or len(poly) < 4:
                continue
            poly_arr = np.array(poly, dtype=np.float32)
            # Filtra tamanho
            x_coords = poly_arr[:, 0]
            y_coords = poly_arr[:, 1]
            if (x_coords.max() - x_coords.min()) < MIN_SIDE_PIXELS or (y_coords.max() - y_coords.min()) < MIN_SIDE_PIXELS:
                continue
            data = info.strip()
            if IGNORE_EMPTY_DECODE and not data:
                continue
            crop = crop_polygon(page_image_bgr, poly_arr, PADDING_FRACTION)
            results.append(QRResult(
                page_number=page_number,
                data=data,
                file_name="",   # preencher depois
                polygon=[(float(x), float(y)) for x, y in poly_arr],
                engine="opencv-multi"
            ))

    # Se multi falhou ou nenhum decode válido, tenta single
    if not results:
        data, single_points, _ = detector.detectAndDecode(page_image_bgr)
        if single_points is not None and len(single_points) >= 4:
            poly_arr = np.array(single_points[0:4], dtype=np.float32)
            x_coords = poly_arr[:, 0]
            y_coords = poly_arr[:, 1]
            if (x_coords.max() - x_coords.min()) >= MIN_SIDE_PIXELS and (y_coords.max() - y_coords.min()) >= MIN_SIDE_PIXELS:
                if (not IGNORE_EMPTY_DECODE) or data.strip():
                    crop = crop_polygon(page_image_bgr, poly_arr, PADDING_FRACTION)
                    results.append(QRResult(
                        page_number=page_number,
                        data=data.strip(),
                        file_name="",
                        polygon=[(float(x), float(y)) for x, y in poly_arr],
                        engine="opencv-single"
                    ))
    return results

def save_results_as_png_and_csv(all_results: List[QRResult]):
    if not all_results:
        print("⚠️ Nenhum QR para salvar.")
        return

    rows = []
    used_names = set()
    for idx, res in enumerate(all_results, start=1):
        base_id = derive_id_from_data(res.data)
        name = base_id
        n = 2
        while name in used_names:
            name = f"{base_id}_{n}"
            n += 1
        used_names.add(name)
        file_name = f"{name}.png"
        res.file_name = file_name

        # Salva imagem
        out_path = PNG_DIR / file_name
        # Converte BGR->RGB antes de PIL
        # (crop foi em BGR se usamos crop_polygon? sim)
        # Precisamos do crop; recortar de novo aqui usando polygon? Vamos armazenar no flow:
        # Melhor: recortar novamente a partir da imagem? Já recortamos antes e perdemos a referência.
        # Adaptação: armazenamos a imagem recortada junto? Sim, vamos refazer: manter crop no resultado?
        # Ajuste: refator – em decode adicionaremos a imagem recortada. (Para não estender muito, reaplico.)
        # Aqui para manter simples:
        # Re-decoder: iremos armazenar o recorte no atributo? => Ajustaremos decode para devolver também crop prontas.
        # Para não reestruturar tudo agora: supomos que iremos adicionar crop no fluxo acima.
        pass

    # Ajuste: precisamos realmente guardar os recortes no momento da detecção. Vamos refatorar rapidamente.

def process_pdf(pdf_path: Path) -> List[QRResult]:
    doc = fitz.open(pdf_path)
    aggregated: List[QRResult] = []
    for i, page in enumerate(doc):
        page_number = i + 1
        pix = page.get_pixmap(dpi=RENDER_DPI)
        page_bgr = pixmap_to_cv(pix)
        page_results = decode_qrs_on_page(page_bgr, page_number)

        # Incluir o recorte real em cada resultado
        for r in page_results:
            # reconstruir polígono para crop
            poly_arr = np.array(r.polygon, dtype=np.float32)
            crop = crop_polygon(page_bgr, poly_arr, PADDING_FRACTION)
            # converter BGR->RGB antes de virar PIL
            crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            r.crop_img = Image.fromarray(crop_rgb)
        if page_results:
            print(f"Página {page_number}: {len(page_results)} QR(s)")
        else:
            print(f"Página {page_number}: nenhum QR")
        aggregated.extend(page_results)
    doc.close()
    return aggregated

def export(all_results: List[QRResult]):
    if not all_results:
        print("⚠️ Nada para exportar.")
        return

    rows = []
    used_names = set()
    for seq_id, res in enumerate(all_results, start=1):
        base_id = derive_id_from_data(res.data)
        final_name = base_id
        n = 2
        while final_name in used_names:
            final_name = f"{base_id}_{n}"
            n += 1
        used_names.add(final_name)

        file_name = f"{final_name}.png"
        res.crop_img.save(PNG_DIR / file_name, "PNG")

        rows.append({
            "seq_id": seq_id,
            "page": res.page_number,
            "engine": res.engine,
            "original_data": res.data,
            "detected_id": final_name,
            "file": file_name
        })

    fieldnames = rows[0].keys()
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"\n📄 CSV: {CSV_PATH}")
    print(f"🖼  PNGs: {PNG_DIR}")
    print(f"Total: {len(rows)}")

def main():
    ensure_dirs()
    print(f"PDF esperado: {PDF_PATH.resolve()}")
    if not PDF_PATH.exists():
        print("❌ PDF não encontrado.")
        sys.exit(1)

    print("➡️ Extraindo QRs (OpenCV apenas)...")
    results = process_pdf(PDF_PATH)
    if not results:
        print("⚠️ Nenhum QR detectado. Tente reduzir RENDER_DPI ou verificar o PDF.")
        return
    export(results)
    print("\n✅ Concluído.")

if __name__ == "__main__":
    main()