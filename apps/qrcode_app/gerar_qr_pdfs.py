import os
import uuid
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import qrcode
from datetime import datetime
import csv

# ================== CONFIGURAÇÕES ==================
OUTPUT_DIR = Path("qrs_pdfs")
OUTPUT_DIR.mkdir(exist_ok=True)

# URL base usada no QR. Cada QR codifica BASE_URL + "/" + Truss_number
BASE_URL = "https://exemplo.com/qr"

# Fonte (tenta em ordem). Ajuste se necessário.
FONT_PATHS = [
    "arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
]

# Tamanho da imagem do QR central na página (px)
QR_SIZE = 800

# Dimensão da página (A4 aproximado @ ~150 dpi)
PAGE_W, PAGE_H = 1240, 1754

# Nome do PDF final consolidado
PDF_UNICO_NAME = "qrs_unificado.pdf"

# Nome do CSV
CSV_NAME = "mapa_qrs.csv"

# Gera também PNGs individuais? (Pode usar depois em outro fluxo)
GERAR_PNGS = True
PNGS_DIR = OUTPUT_DIR / "pngs"
# ===================================================

def pick_font(size):
    for fp in FONT_PATHS:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    return ImageFont.load_default()

def gerar_qr(data: str, size: int = QR_SIZE) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        box_size=10,
        border=4,
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    return img.resize((size, size))

def montar_pagina(qr_img: Image.Image, titulo: str, subtitulo: str | None = None) -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    draw = ImageDraw.Draw(page)

    # Centraliza o QR
    qr_x = (PAGE_W - qr_img.width) // 2
    qr_y = (PAGE_H - qr_img.height) // 2 - 120
    page.paste(qr_img, (qr_x, qr_y), mask=qr_img)

    font_title = pick_font(60)
    font_sub = pick_font(40)

    # Título (ex.: T001)
    tw = draw.textlength(titulo, font=font_title)
    draw.text(((PAGE_W - tw) // 2, qr_y + qr_img.height + 30), titulo, fill="black", font=font_title)

    # Subtítulo opcional (ex.: URL ou outra info)
    if subtitulo:
        sw = draw.textlength(subtitulo, font=font_sub)
        draw.text(((PAGE_W - sw) // 2, qr_y + qr_img.height + 120), subtitulo, fill="black", font=font_sub)

    return page

def gerar_valores_aleatorios():
    """
    Gera alguns valores plausíveis para colunas.
    Ajuste conforme necessidade ou troque por valores fixos se preferir.
    """
    qnty = random.randint(1, 12)     # Qnty
    ply = random.choice([1, 2, 3, 4])
    size_ft = random.choice([6, 8, 10, 12, 14, 16])
    status = random.choice(["Completed", "Ongoing", "On Hold"])
    return qnty, ply, size_ft, status

def main(qty: int = 10):
    if GERAR_PNGS:
        PNGS_DIR.mkdir(exist_ok=True)

    registros_csv = []
    paginas_pdf = []

    now_iso = datetime.utcnow().isoformat()
    # Se quiser Date_Update vazio, basta setar date_update = ""
    # Aqui coloco igual para ambos (pode personalizar)
    for i in range(1, qty + 1):
        # Truss_number no formato T001, T002...
        truss_number = f"T{i:03d}"

        # Geração de valores para colunas
        qnty, ply, size_ft, status = gerar_valores_aleatorios()

        # QR codifica a URL com o truss_number
        url_qr = f"{BASE_URL}/{truss_number}"

        qr_img = gerar_qr(url_qr)

        # Página exibe o truss_number grande e pode opcionalmente mostrar a URL
        page = montar_pagina(qr_img, titulo=truss_number, subtitulo=url_qr)
        paginas_pdf.append(page)

        # Salva PNG individual (opcional)
        if GERAR_PNGS:
            png_path = PNGS_DIR / f"{truss_number}.png"
            page.save(png_path, "PNG")

        # Monta registro CSV no formato solicitado
        registro = {
            "id": i,
            "Truss_number": truss_number,
            "Truss_type": "",              # vazio (ajuste se precisar)
            "Qnty": qnty,
            "ply": ply,
            "Job_Reference": "Av. Central, 789",
            "Size (ft)": size_ft,
            "Status": status,
            "User": "",                    # vazio
            "Date_Insert": now_iso,
            "Date_Update": now_iso
        }
        registros_csv.append(registro)
        print(f"✅ QR preparado: {truss_number} (URL: {url_qr})")

    # Salva PDF único
    if paginas_pdf:
        pdf_path = OUTPUT_DIR / PDF_UNICO_NAME
        # Primeiro convertido em RGB (garantia)
        rgb_pages = [p.convert("RGB") for p in paginas_pdf]
        rgb_pages[0].save(pdf_path, save_all=True, append_images=rgb_pages[1:])
        print(f"\n📄 PDF único gerado: {pdf_path}")

    # Salva CSV
    csv_path = OUTPUT_DIR / CSV_NAME
    fieldnames = [
        "id","Truss_number","Truss_type","Qnty","ply",
        "Job_Reference","Size (ft)","Status","User",
        "Date_Insert","Date_Update"
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(registros_csv)
    print(f"🗂  CSV gerado: {csv_path}")

    print("\n🎉 Concluído.")

if __name__ == "__main__":
    # Ajuste aqui a quantidade desejada
    main(10)