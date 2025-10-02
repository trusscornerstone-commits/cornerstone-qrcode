import os
import json
import pandas as pd
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import shutil

# ================== CONFIG ==================
EXTRACT_CSV = "qrs_extracao/mapa_qrs.csv"
PNG_DIR     = Path("qrs_extracao/qrs_png")
OUTPUT_DIR  = Path("templates/qrcodes")

# JSONs (opcional)
EXPORT_JSON = True
TRUSS_JSON_DIR = Path("static/truss-data")

# Layout 4x6 @ 300 DPI
FINAL_WIDTH  = 1200
FINAL_HEIGHT = 1800
DPI = 300

QR_MAIN_SIZE  = 400
QR_SMALL_SIZE = 200

LOGO_PATH = "cornerstone_logo.png"
EMPRESA_ENDERECO = "Rua Exemplo, 123 - Cidade/UF"
EMPRESA_TEL      = "(11) 99999-8888"

SHOW_JOB_REFERENCE = False  # sem job nesse fluxo (não temos ainda)
# Se no futuro quiser usar a URL/ dado para extrair algo, pode alterar aqui.

FONT_CANDIDATES = [
    "arialbd.ttf",
    "arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
]

# Se você quiser usar o original_data no QR principal ao regenerar (não recomendado aqui)
REGENERAR_QR = False  # mantemos as imagens extraídas
# ============================================

def pick_font(size, bold=False):
    for fp in FONT_CANDIDATES:
        name = fp.lower()
        if bold and not any(x in name for x in ["bd","bold"]):
            continue
        if not bold and any(x in name for x in ["bd","bold"]):
            continue
        try:
            return ImageFont.truetype(fp, size)
        except:
            pass
    return ImageFont.load_default()

def carregar_logo(max_w=250):
    if not os.path.exists(LOGO_PATH):
        raise FileNotFoundError(f"Logo não encontrado: {LOGO_PATH}")
    logo = Image.open(LOGO_PATH).convert("RGBA")
    logo.thumbnail((max_w, max_w))
    return logo

def carregar_qr_image(file_name: str, size: int) -> Image.Image:
    p = PNG_DIR / file_name
    if not p.exists():
        raise FileNotFoundError(f"QR PNG não encontrado: {p}")
    img = Image.open(p).convert("RGBA")
    # Garantir quadrado (central crop se necessário)
    w, h = img.size
    if w != h:
        side = min(w, h)
        left = (w - side)//2
        top = (h - side)//2
        img = img.crop((left, top, left+side, top+side))
    img = img.resize((size, size), Image.NEAREST)
    return img

def desenhar_faixa_horizontal(base_img, truss_id_display, logo, qr_small, y_pos):
    faixa_altura = qr_small.height
    bloco_w, bloco_h = FINAL_WIDTH - 200, faixa_altura
    bloco = Image.new("RGBA", (bloco_w, bloco_h), "white")
    draw_b = ImageDraw.Draw(bloco)

    font_label  = pick_font(22, bold=False)
    font_number = pick_font(85, bold=True)

    # Logo
    logo_y = (bloco_h - logo.height)//2
    bloco.paste(logo, (20, logo_y), mask=logo)

    # QR pequeno
    bloco.paste(qr_small, (bloco_w - qr_small.width - 20,
                           (bloco_h - qr_small.height)//2), mask=qr_small)

    # Textos
    label_text = "Truss ID:"
    lw = draw_b.textlength(label_text, font=font_label)
    draw_b.text(((bloco_w - lw)//2, 5), label_text, fill="black", font=font_label)

    nw = draw_b.textlength(truss_id_display, font=font_number)
    draw_b.text(((bloco_w - nw)//2, 35), truss_id_display, fill="black", font=font_number)

    x = (FINAL_WIDTH - bloco_w)//2
    base_img.paste(bloco, (x, y_pos), mask=bloco)

def desenhar_centro(base_img, truss_id_display, job_reference, logo, qr_main):
    bloco_w, bloco_h = 950, 400
    bloco = Image.new("RGBA", (bloco_w, bloco_h), "white")

    # QR grande
    qr_x = 10
    qr_y = (bloco_h - qr_main.height)//2
    bloco.paste(qr_main, (qr_x, qr_y), mask=qr_main)

    # Coluna rotacionada (logo + ID + endereço)
    sub_w, sub_h = 400, 500
    sub = Image.new("RGBA", (sub_w, sub_h), "white")
    ds = ImageDraw.Draw(sub)

    logo_c = carregar_logo(320)
    lx = (sub_w - logo_c.width)//2
    ly = 10
    sub.paste(logo_c, (lx, ly), mask=logo_c)

    font_big   = pick_font(120, bold=True)
    font_med   = pick_font(30, bold=False)
    font_small = pick_font(22, bold=False)

    ty = ly + logo_c.height + 30

    if SHOW_JOB_REFERENCE and job_reference:
        job_text = f"Job: {job_reference}"
        jw = ds.textlength(job_text, font=font_med)
        ds.text(((sub_w - jw)//2, ty), job_text, fill="black", font=font_med)
        ty += 60

    label_text = "Truss ID:"
    lw = ds.textlength(label_text, font=font_med)
    ds.text(((sub_w - lw)//2, ty), label_text, fill="black", font=font_med)
    ty += 45

    nw = ds.textlength(truss_id_display, font=font_big)
    ds.text(((sub_w - nw)//2, ty), truss_id_display, fill="black", font=font_big)
    ty += 140

    end_text = f"{EMPRESA_ENDERECO}\n{EMPRESA_TEL}"
    ds.multiline_text(((sub_w - ds.textlength(EMPRESA_ENDERECO,font=font_small))//2, ty),
                      end_text, fill="black", font=font_small, align="center", spacing=6)

    sub_rot = sub.rotate(90, expand=True)
    logo_x = qr_x + qr_main.width + 30
    logo_y = (bloco_h - sub_rot.height)//2
    bloco.paste(sub_rot, (logo_x, logo_y), mask=sub_rot)

    # Posiciona no centro
    x = (FINAL_WIDTH - bloco_w)//2
    y = (FINAL_HEIGHT - bloco_h)//2
    base_img.paste(bloco, (x, y), mask=bloco)

def exportar_json(df):
    if not EXPORT_JSON:
        return
    TRUSS_JSON_DIR.mkdir(parents=True, exist_ok=True)
    index = {}
    for _, row in df.iterrows():
        sid = int(row["seq_id"])
        data = {
            "id": sid,
            "detected_id": row.get("detected_id",""),
            "original_data": row.get("original_data",""),
            "file": row.get("file",""),
            "engine": row.get("engine",""),
            "page": int(row.get("page",0)),
            "occurrence_for_data": int(row.get("occurrence_for_data",1))
        }
        p = TRUSS_JSON_DIR / f"{sid}.json"
        with open(p,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
        index[str(sid)] = f"/static/truss-data/{sid}.json"
    with open(TRUSS_JSON_DIR/"index.json","w",encoding="utf-8") as f:
        json.dump(index,f,ensure_ascii=False,indent=2)
    print(f"📦 JSONs exportados em: {TRUSS_JSON_DIR}")

def load_mapping():
    if not os.path.exists(EXTRACT_CSV):
        raise FileNotFoundError(f"CSV de extração não encontrado: {EXTRACT_CSV}")
    df = pd.read_csv(EXTRACT_CSV)
    obrig = {"seq_id","file","detected_id"}
    if not obrig.issubset(df.columns):
        raise ValueError(f"CSV sem colunas {obrig}. Colunas: {df.columns.tolist()}")
    df = df.sort_values("seq_id").reset_index(drop=True)
    # Se quiser adicionar alguma coluna de quantidade no futuro, adapte aqui:
    if "quantity" not in df.columns:
        df["quantity"] = 1
    return df

def gerar_etiquetas(pdf_name="labels.pdf"):
    df = load_mapping()
    exportar_json(df)

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logo_small = carregar_logo(250)
    imagens_pdf = []

    for _, row in df.iterrows():
        truss_display = str(row["detected_id"])
        file_name = row["file"]
        qty = int(row.get("quantity",1))
        original_data = row.get("original_data","")

        for i in range(1, qty+1):
            base = Image.new("RGBA",(FINAL_WIDTH,FINAL_HEIGHT),"white")

            if REGENERAR_QR and original_data:
                # Se quiser regenerar com o conteúdo original (não recomendado se quiser fiel à imagem)
                import qrcode
                qr_big = qrcode.make(original_data).resize((QR_MAIN_SIZE,QR_MAIN_SIZE))
                qr_big = qr_big.convert("RGBA")
                qr_small = qr_big.resize((QR_SMALL_SIZE,QR_SMALL_SIZE), Image.NEAREST)
            else:
                qr_big = carregar_qr_image(file_name, QR_MAIN_SIZE)
                qr_small = carregar_qr_image(file_name, QR_SMALL_SIZE)

            desenhar_faixa_horizontal(base, truss_display, logo_small, qr_small, 80)
            desenhar_centro(base, truss_display, None, logo_small, qr_big)
            desenhar_faixa_horizontal(base, truss_display, logo_small, qr_small,
                                      FINAL_HEIGHT - QR_SMALL_SIZE - 80)

            fname = f"label_{row['seq_id']}_{truss_display}_{i}.png"
            out_path = OUTPUT_DIR / fname
            base.save(out_path, dpi=(DPI,DPI))
            imagens_pdf.append(base.convert("RGB"))
            print(f"✅ Etiqueta gerada: {fname}")

    if imagens_pdf:
        pdf_path = OUTPUT_DIR / pdf_name
        imagens_pdf[0].save(pdf_path, save_all=True, append_images=imagens_pdf[1:])
        print(f"\n📄 PDF final: {pdf_path}")

    print("\n🎉 Concluído. Etiquetas em:", OUTPUT_DIR)

if __name__ == "__main__":
    gerar_etiquetas()