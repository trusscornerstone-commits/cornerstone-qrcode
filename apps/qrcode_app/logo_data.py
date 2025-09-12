import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os

# === Configurações ===
CSV_PATH = "trusses.csv"
OUTPUT_DIR = "qrcodes"
API_BASE_URL = "https://api.sistema-trusses.com/truss"
LOGO_PATH = "cornerstone_logo.png"
FONT_PATH = "arial.ttf"

FINAL_WIDTH = 1200    # 4" x 300 dpi
FINAL_HEIGHT = 1800   # 6" x 300 dpi
DPI = 300
QR_SIZE = int(FINAL_WIDTH * 0.18)

EMPRESA_ENDERECO = "Rua Exemplo, 123 - Cidade/UF"
EMPRESA_TEL = "(11) 99999-8888"


# === Funções auxiliares ===

def gerar_qrcode(truss_id, api_base_url, size=QR_SIZE):
    qr_data = f"{api_base_url}/{truss_id}"
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    return img_qr.resize((size, size))


def gerar_texto_vertical(truss_name, font_label, font_value):
    """Cria imagem com 'Truss ID:' pequeno e valor grande, já pronto para rotacionar"""
    label_text = "Truss ID:"
    value_text = str(truss_name)

    # cria label
    tmp = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
    d = ImageDraw.Draw(tmp)
    bbox_label = d.textbbox((0, 0), label_text, font=font_label)
    label_img = Image.new("RGBA", (bbox_label[2], bbox_label[3]), (255, 255, 255, 0))
    d = ImageDraw.Draw(label_img)
    d.text((0, 0), label_text, fill="black", font=font_label)

    # cria valor
    bbox_value = d.textbbox((0, 0), value_text, font=font_value)
    value_img = Image.new("RGBA", (bbox_value[2], bbox_value[3]), (255, 255, 255, 0))
    d = ImageDraw.Draw(value_img)
    d.text((0, 0), value_text, fill="black", font=font_value)

    # combinar
    combined_h = label_img.height + value_img.height + 5
    combined_w = max(label_img.width, value_img.width)
    combined = Image.new("RGBA", (combined_w, combined_h), (255, 255, 255, 0))
    combined.paste(label_img, (0, 0), label_img)
    combined.paste(value_img, (0, label_img.height + 5), value_img)

    return combined.rotate(90, expand=True), combined.rotate(270, expand=True)


def carregar_logo(path, max_width):
    logo = Image.open(path).convert("RGBA")
    logo.thumbnail((max_width, max_width))
    return logo


def desenhar_textos(draw, row, logo_y, logo_h, final_width, font, font_small):
    """Desenha Job Number, Truss ID central e endereço"""
    job_number = row.get("job_number", "")
    job_y = logo_y + logo_h + 15  # espaço após logo

    # Job Number
    if job_number:
        job_text = f"Job Number: {job_number}"
        bbox = draw.textbbox((0, 0), job_text, font=font)
        job_w = bbox[2] - bbox[0]
        job_x = (final_width - job_w) // 2
        draw.text((job_x, job_y), job_text, fill="black", font=font)
        job_y += 35  # espaço extra abaixo do job number

    # Truss ID central
    font_label = ImageFont.truetype("arial.ttf", 10)
    font_value = ImageFont.truetype("arialbd.ttf", 65)
    label_text = "Truss ID:"
    value_text = str(row["truss_number"])

    bbox_label = draw.textbbox((0, 0), label_text, font=font_label)
    bbox_value = draw.textbbox((0, 0), value_text, font=font_value)

    value_x = (final_width - (bbox_value[2] - bbox_value[0])) // 2
    value_y = job_y + 25
    label_x = (final_width - (bbox_label[2] - bbox_label[0])) // 2
    label_y = value_y - (bbox_label[3] - bbox_label[1]) - 5

    draw.text((label_x, label_y), label_text, fill="black", font=font_label)
    draw.text((value_x, value_y), value_text, fill="black", font=font_value)

    # Endereço/contato
    empresa_text = f"{EMPRESA_ENDERECO}\n{EMPRESA_TEL}"
    lines = empresa_text.split("\n")
    y = value_y + (bbox_value[3] - bbox_value[1]) + 30

    # Fonte menor para caber
    font_address = ImageFont.truetype("arial.ttf", 17)

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_address)
        text_w = bbox[2] - bbox[0]
        text_x = (final_width - text_w) // 2
        draw.text((text_x, y), line, fill="black", font=font_address)
        y += 20


# === Função principal ===

def gerar_qrcodes_com_logo(csv_path, output_dir, api_base_url, logo_path, font_path):
    df = pd.read_csv(csv_path)
    os.makedirs(output_dir, exist_ok=True)

    try:
        font = ImageFont.truetype(font_path, 25)
        font_small = ImageFont.truetype(font_path, 7)
    except:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()

    for _, row in df.iterrows():
        truss_id = row["id"]
        truss_name = row["truss_number"]

        # base
        img_final = Image.new("RGBA", (FINAL_WIDTH, FINAL_HEIGHT), "white")

        # QR Code central
        img_qr = gerar_qrcode(truss_id, api_base_url)
        qr_x = (FINAL_WIDTH - img_qr.width) // 2
        qr_y = 40
        img_final.paste(img_qr, (qr_x, qr_y))

        # Texto vertical
        font_side_label = ImageFont.truetype("arial.ttf", 12)
        font_side_value = ImageFont.truetype("arialbd.ttf", 60)
        text_left, text_right = gerar_texto_vertical(truss_name, font_side_label, font_side_value)

        MARGEM_BORDA = 30
        y_vert = (FINAL_HEIGHT - text_left.height) // 2
        img_final.paste(text_left, (MARGEM_BORDA, y_vert), mask=text_left)
        img_final.paste(text_right, (FINAL_WIDTH - text_right.width - MARGEM_BORDA, y_vert), mask=text_right)

        # Logos laterais (maiores)
        logo_side = carregar_logo(logo_path, 130)
        logo_left = logo_side.rotate(90, expand=True)
        logo_right = logo_side.rotate(270, expand=True)

        PADDING_EXTRA = 80
        img_final.paste(
            logo_left,
            (MARGEM_BORDA, y_vert + text_left.height + PADDING_EXTRA),
            mask=logo_left
        )
        img_final.paste(
            logo_right,
            (FINAL_WIDTH - logo_right.width - MARGEM_BORDA, y_vert + text_right.height + PADDING_EXTRA),
            mask=logo_right
        )

        # Logo central (maior)
        logo = carregar_logo(logo_path, int(FINAL_WIDTH * 0.28))
        logo_x = (FINAL_WIDTH - logo.width) // 2
        logo_y = qr_y + img_qr.height + 10
        img_final.paste(logo, (logo_x, logo_y), mask=logo)

        # QRCodes laterais
        qr_side = gerar_qrcode(truss_id, api_base_url, size=120)
        qr_side_y = y_vert - qr_side.height - 100 #TODO

        # Esquerda
        qr_side_left_x = MARGEM_BORDA
        img_final.paste(qr_side, (qr_side_left_x, qr_side_y))

        # Direita
        qr_side_right_x = FINAL_WIDTH - qr_side.width - MARGEM_BORDA
        img_final.paste(qr_side, (qr_side_right_x, qr_side_y))

        # Textos centrais
        draw = ImageDraw.Draw(img_final)
        desenhar_textos(draw, row, logo_y, logo.height, FINAL_WIDTH, font, font_small)

        # Salvar
        file_name = f"truss_{truss_id}.png"
        img_final.save(os.path.join(output_dir, file_name), dpi=(DPI, DPI))
        print(f"✅ QR Code gerado: {file_name}")

    print(f"\n🎉 Todos os QR Codes foram salvos em: {output_dir}")


if __name__ == "__main__":
    gerar_qrcodes_com_logo(CSV_PATH, OUTPUT_DIR, API_BASE_URL, LOGO_PATH, FONT_PATH)
