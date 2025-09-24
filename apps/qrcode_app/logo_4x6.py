import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
import shutil
import json
from pathlib import Path

# === Configurações ===
CSV_PATH = "trusses.csv"
OUTPUT_DIR = "templates/qrcodes"

# Recomendado: QR aponta para a rota WEB do Django
WEB_BASE_URL = os.getenv("WEB_BASE_URL", "https://cornerstone-app.onrender.com/truss")

LOGO_PATH = "cornerstone_logo.png"
FONT_PATH = "arial.ttf"

# JSONs estáticos consumidos pelo template
APP_DIR = Path(__file__).resolve().parent
TRUSS_JSON_DIR = APP_DIR / "static" / "truss-data"

FINAL_WIDTH = 1200
FINAL_HEIGHT = 1800
DPI = 300

QR_MAIN_SIZE = 500
QR_SMALL_SIZE = 200

EMPRESA_ENDERECO = "Rua Exemplo, 123 - Cidade/UF"
EMPRESA_TEL = "(11) 99999-8888"

def gerar_qrcode(truss_id, base_url, size):
    qr_data = f"{base_url}/{truss_id}"
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    return img_qr.resize((size, size))

def carregar_logo(path, max_width):
    logo = Image.open(path).convert("RGBA")
    logo.thumbnail((max_width, max_width))
    return logo

def desenhar_faixa_horizontal(base_img, truss_number, logo, qr_small, y_pos):
    faixa_altura = qr_small.height
    bloco_w, bloco_h = FINAL_WIDTH - 200, faixa_altura
    bloco = Image.new("RGBA", (bloco_w, bloco_h), "white")
    draw_b = ImageDraw.Draw(bloco)

    font_label = ImageFont.truetype("arial.ttf", 22)
    font_number = ImageFont.truetype("arialbd.ttf", 85)

    logo_y = (bloco_h - logo.height) // 2
    bloco.paste(logo, (20, logo_y), mask=logo)

    bloco.paste(qr_small, (bloco_w - qr_small.width - 20, (bloco_h - qr_small.height) // 2), mask=qr_small)

    label_text = "Truss ID:"
    lw = draw_b.textlength(label_text, font=font_label)
    draw_b.text(((bloco_w - lw) // 2, 5), label_text, fill="black", font=font_label)

    nw = draw_b.textlength(str(truss_number), font=font_number)
    draw_b.text(((bloco_w - nw) // 2, 35), str(truss_number), fill="black", font=font_number)

    x = (FINAL_WIDTH - bloco_w) // 2
    base_img.paste(bloco, (x, y_pos), mask=bloco)

def desenhar_centro(draw, base_img, row, logo, EMPRESA_ENDERECO, EMPRESA_TEL):
    truss_id = row["id"]
    truss_number = str(row["truss_number"])
    job_number = row.get("job_number", "")

    bloco_w, bloco_h = 950, 400
    bloco = Image.new("RGBA", (bloco_w, bloco_h), "white")

    qr_main = gerar_qrcode(truss_id, WEB_BASE_URL, 250)
    qr_x = 10
    qr_y = (bloco_h - qr_main.height) // 2
    bloco.paste(qr_main, (qr_x, qr_y), mask=qr_main)

    sub_w, sub_h = 400, 500
    sub_bloco = Image.new("RGBA", (sub_w, sub_h), "white")
    draw_s = ImageDraw.Draw(sub_bloco)

    logo_c = carregar_logo(LOGO_PATH, 400)
    lx = (sub_w - logo_c.width) // 2
    ly = 10
    sub_bloco.paste(logo_c, (lx, ly), mask=logo_c)

    font_big = ImageFont.truetype("arialbd.ttf", 120)
    font_med = ImageFont.truetype("arial.ttf", 30)
    ty = ly + logo_c.height + 40

    if job_number:
        job_text = f"Job: {job_number}"
        jw = draw_s.textlength(job_text, font=font_med)
        draw_s.text(((sub_w - jw) // 2, ty), job_text, fill="black", font=font_med)
        ty += 70

    label_text = "Truss ID:"
    lw = draw_s.textlength(label_text, font=font_med)
    draw_s.text(((sub_w - lw) // 2, ty), label_text, fill="black", font=font_med)
    ty += 50

    nw = draw_s.textlength(truss_number, font=font_big)
    draw_s.text(((sub_w - nw) // 2, ty), truss_number, fill="black", font=font_big)

    sub_rot = sub_bloco.rotate(90, expand=True)

    logo_x = qr_x + qr_main.width + 20
    logo_y = (bloco_h - sub_rot.height) // 2
    bloco.paste(sub_rot, (logo_x, logo_y), mask=sub_rot)

    font_small = ImageFont.truetype("arial.ttf", 22)
    end_text = f"{EMPRESA_ENDERECO}\n{EMPRESA_TEL}"

    dummy = Image.new("RGBA", (1, 1), "white")
    ddraw = ImageDraw.Draw(dummy)
    bbox = ddraw.textbbox((0, 0), end_text, font=font_small)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    sub_end = Image.new("RGBA", (text_w + 80, text_h + 60), "white")
    draw_e = ImageDraw.Draw(sub_end)
    end_x = (sub_end.width - text_w) // 2
    end_y = (sub_end.height - text_h) // 2
    draw_e.text((end_x, end_y), end_text, fill="black", font=font_small, align="center")

    sub_end_rot = sub_end.rotate(90, expand=True)

    end_x = bloco.width - sub_end_rot.width - 5
    end_y = (bloco_h - sub_end_rot.height) // 2
    bloco.paste(sub_end_rot, (end_x, end_y), mask=sub_end_rot)

    x = (FINAL_WIDTH - bloco.width) // 2
    y = (FINAL_HEIGHT - bloco.height) // 2
    base_img.paste(bloco, (x, y), mask=bloco)

def exportar_json_por_truss(df, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    index = {}
    for _, row in df.iterrows():
        try:
            truss_id = int(row["id"])
        except Exception:
            continue
        data = {
            "id": truss_id,
            "job_number": row.get("job_number", ""),
            "truss_number": str(row.get("truss_number", "")),
            "tipo": row.get("tipo", ""),
            "quantidade": int(row.get("quantidade", 0)) if str(row.get("quantidade", "")).isdigit() else row.get("quantidade", ""),
            "ply": row.get("ply", ""),
            "endereco": row.get("endereco", ""),
            "tamanho": row.get("tamanho", ""),
            "status": row.get("status", ""),
        }
        path = out_dir / f"{truss_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        index[str(truss_id)] = f"/static/truss-data/{truss_id}.json"
    with open(out_dir / "index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"📦 JSONs exportados em: {out_dir}")

def gerar_etiquetas(csv_path, output_dir, pdf_name="labels.pdf"):
    df = pd.read_csv(csv_path)

    # Exporta JSONs consumidos pelo web
    exportar_json_por_truss(df, TRUSS_JSON_DIR)

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    imagens_pdf = []

    for _, row in df.iterrows():
        truss_id = row["id"]
        quantidade = int(row.get("quantidade", 1))

        for i in range(quantidade):
            img_final = Image.new("RGBA", (FINAL_WIDTH, FINAL_HEIGHT), "white")
            draw = ImageDraw.Draw(img_final)

            logo_small = carregar_logo(LOGO_PATH, 250)
            qr_small = gerar_qrcode(truss_id, WEB_BASE_URL, QR_SMALL_SIZE)

            desenhar_faixa_horizontal(img_final, row["truss_number"], logo_small, qr_small, 80)
            desenhar_centro(draw, img_final, row, logo_small, EMPRESA_ENDERECO, EMPRESA_TEL)
            desenhar_faixa_horizontal(img_final, row["truss_number"], logo_small, qr_small, FINAL_HEIGHT - QR_SMALL_SIZE - 80)

            file_name = f"truss_{truss_id}_{i+1}.png"
            path_img = os.path.join(output_dir, file_name)
            img_final.save(path_img, dpi=(DPI, DPI))
            print(f"✅ Etiqueta gerada: {file_name}")

            imagens_pdf.append(img_final.convert("RGB"))

    if imagens_pdf:
        pdf_path = os.path.join(output_dir, pdf_name)
        imagens_pdf[0].save(pdf_path, save_all=True, append_images=imagens_pdf[1:])
        print(f"\n📄 PDF gerado com todas as etiquetas: {pdf_path}")

    print(f"\n🎉 Todas as etiquetas foram salvas em: {output_dir}")

if __name__ == "__main__":
    gerar_etiquetas(CSV_PATH, OUTPUT_DIR)