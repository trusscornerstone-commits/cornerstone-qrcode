import os
import json
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple, Union
from decimal import Decimal

import qrcode
from PIL import Image, ImageDraw, ImageFont

try:
    import pandas as pd  # Opcional: só exigido se usar CSV
except Exception:
    pd = None  # type: ignore

# ================== CONFIG BÁSICA / CONSTANTES ==================

FINAL_WIDTH = 1200
FINAL_HEIGHT = 1800
DPI = 300

QR_MAIN_SIZE = 500
QR_SMALL_SIZE = 200

# Tentar fontes comuns; se não achar, cai no default do Pillow
FONT_CANDIDATES_REG = [
    "arial.ttf",
    "Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
FONT_CANDIDATES_BOLD = [
    "arialbd.ttf",
    "Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

# ================================================================

class FontBundle:
    def __init__(self, reg22, reg30, bold85, bold120):
        self.reg22 = reg22
        self.reg30 = reg30
        self.bold85 = bold85
        self.bold120 = bold120


def _load_first_font(candidates: Sequence[str], size: int):
    last_exc = None
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception as e:
            last_exc = e
    # Fallback
    try:
        return ImageFont.load_default()
    except Exception:
        raise last_exc or RuntimeError("Nenhuma fonte encontrada.")


def build_fonts() -> FontBundle:
    return FontBundle(
        reg22=_load_first_font(FONT_CANDIDATES_REG, 22),
        reg30=_load_first_font(FONT_CANDIDATES_REG, 30),
        bold85=_load_first_font(FONT_CANDIDATES_BOLD, 85),
        bold120=_load_first_font(FONT_CANDIDATES_BOLD, 120),
    )


def carregar_logo(path: Path, max_width: int) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(f"Logo não encontrado em {path}")
    logo = Image.open(path).convert("RGBA")
    logo.thumbnail((max_width, max_width))
    return logo


def gerar_qrcode(truss_id: Union[int, str], base_url: str, size: int) -> Image.Image:
    qr_data = f"{base_url}/{truss_id}"
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    return img_qr.resize((size, size))


def _desenhar_faixa_horizontal(
    base_img: Image.Image,
    truss_number: str,
    logo_small: Image.Image,
    qr_small: Image.Image,
    y_pos: int,
    fonts: FontBundle,
):
    faixa_altura = qr_small.height
    bloco_w, bloco_h = FINAL_WIDTH - 200, faixa_altura
    bloco = Image.new("RGBA", (bloco_w, bloco_h), "white")
    draw_b = ImageDraw.Draw(bloco)

    logo_y = (bloco_h - logo_small.height) // 2
    bloco.paste(logo_small, (20, logo_y), mask=logo_small)

    bloco.paste(
        qr_small,
        (bloco_w - qr_small.width - 20, (bloco_h - qr_small.height) // 2),
        mask=qr_small,
    )

    label_text = "Truss ID:"
    lw = draw_b.textlength(label_text, font=fonts.reg22)
    draw_b.text(((bloco_w - lw) // 2, 5), label_text, fill="black", font=fonts.reg22)

    tn = str(truss_number or "")
    nw = draw_b.textlength(tn, font=fonts.bold85)
    draw_b.text(((bloco_w - nw) // 2, 35), tn, fill="black", font=fonts.bold85)

    x = (FINAL_WIDTH - bloco_w) // 2
    base_img.paste(bloco, (x, y_pos), mask=bloco)


def _desenhar_centro(
    base_img: Image.Image,
    truss_id: int,
    truss_number: str,
    job_number: str,
    logo_path: Path,
    base_url: str,
    empresa_endereco: str,
    empresa_tel: str,
    fonts: FontBundle,
):
    bloco_w, bloco_h = 950, 400
    bloco = Image.new("RGBA", (bloco_w, bloco_h), "white")

    qr_main = gerar_qrcode(truss_id, base_url, 250)
    qr_x = 10
    qr_y = (bloco_h - qr_main.height) // 2
    bloco.paste(qr_main, (qr_x, qr_y), mask=qr_main)

    # Sub-bloco rotacionado
    sub_w, sub_h = 400, 500
    sub_bloco = Image.new("RGBA", (sub_w, sub_h), "white")
    draw_s = ImageDraw.Draw(sub_bloco)

    logo_c = carregar_logo(logo_path, 400)
    lx = (sub_w - logo_c.width) // 2
    ly = 10
    sub_bloco.paste(logo_c, (lx, ly), mask=logo_c)

    ty = ly + logo_c.height + 40

    if job_number:
        job_text = f"Job: {job_number}"
        jw = draw_s.textlength(job_text, font=fonts.reg30)
        draw_s.text(((sub_w - jw) // 2, ty), job_text, fill="black", font=fonts.reg30)
        ty += 70

    label_text = "Truss ID:"
    lw = draw_s.textlength(label_text, font=fonts.reg30)
    draw_s.text(((sub_w - lw) // 2, ty), label_text, fill="black", font=fonts.reg30)
    ty += 50

    tn = truss_number or ""
    nw = draw_s.textlength(tn, font=fonts.bold120)
    draw_s.text(((sub_w - nw) // 2, ty), tn, fill="black", font=fonts.bold120)

    sub_rot = sub_bloco.rotate(90, expand=True)
    logo_x = qr_x + qr_main.width + 20
    logo_y = (bloco_h - sub_rot.height) // 2
    bloco.paste(sub_rot, (logo_x, logo_y), mask=sub_rot)

    # Endereço
    font_small = fonts.reg22
    end_text = f"{empresa_endereco}\n{empresa_tel}"
    dummy = Image.new("RGBA", (1, 1), "white")
    ddraw = ImageDraw.Draw(dummy)
    bbox = ddraw.textbbox((0, 0), end_text, font=font_small)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

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


def serialize_value(v):
    if isinstance(v, Decimal):
        # Mantemos como string para não perder precisão e evitar float estranho
        return str(v)
    if v is None:
        return ""
    return v


def exportar_json(qs_like: Iterable[dict], json_dir: Path, base_public_path: str = "/static/truss-data"):
    json_dir.mkdir(parents=True, exist_ok=True)
    index = {}
    for item in qs_like:
        tid = int(item["id"])
        data = {
            "id": tid,
            "job_number": serialize_value(item.get("job_number")),
            "truss_number": str(serialize_value(item.get("truss_number"))),
            "tipo": serialize_value(item.get("tipo")),
            "quantidade": serialize_value(item.get("quantidade")),
            "ply": serialize_value(item.get("ply")),
            "endereco": serialize_value(item.get("endereco")),
            "tamanho": serialize_value(item.get("tamanho")),
            "status": serialize_value(item.get("status")),
        }
        path = json_dir / f"{tid}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        index[str(tid)] = f"{base_public_path}/{tid}.json"

    with (json_dir / "index.json").open("w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def _sanitize_quantidade(q):
    try:
        v = int(q)
        return v if v > 0 else 1
    except Exception:
        return 1


def gerar_imagens_e_pdf(
    registros: List[dict],
    output_dir: Path,
    logo_path: Path,
    base_url: str,
    empresa_endereco: str,
    empresa_tel: str,
    pdf_name: str = "labels.pdf",
    clean: bool = True,
) -> Tuple[int, int, Optional[Path]]:
    """
    registros: lista de dicionários com campos do Truss.
    Retorna (num_trusses, num_imagens, caminho_pdf|None)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    if clean:
        # Limpa apenas arquivos gerados antes
        for f in output_dir.glob("truss_*.png"):
            try:
                f.unlink()
            except Exception:
                pass
        for f in output_dir.glob("*.pdf"):
            try:
                f.unlink()
            except Exception:
                pass

    fonts = build_fonts()
    logo_small_cache = carregar_logo(logo_path, 250)

    imagens_pdf: List[Image.Image] = []
    total_imgs = 0

    for reg in registros:
        tid = int(reg["id"])
        truss_number = str(reg.get("truss_number") or "")
        job_number = reg.get("job_number") or ""
        quantidade = _sanitize_quantidade(reg.get("quantidade"))

        for i in range(quantidade):
            img_final = Image.new("RGBA", (FINAL_WIDTH, FINAL_HEIGHT), "white")
            qr_small = gerar_qrcode(tid, base_url, QR_SMALL_SIZE)

            _desenhar_faixa_horizontal(
                img_final, truss_number, logo_small_cache, qr_small, 80, fonts
            )
            _desenhar_centro(
                img_final,
                tid,
                truss_number,
                job_number,
                logo_path,
                base_url,
                empresa_endereco,
                empresa_tel,
                fonts,
            )
            _desenhar_faixa_horizontal(
                img_final,
                truss_number,
                logo_small_cache,
                qr_small,
                FINAL_HEIGHT - QR_SMALL_SIZE - 80,
                fonts,
            )

            file_name = f"truss_{tid}_{i+1}.png"
            img_path = output_dir / file_name
            img_final.save(img_path, dpi=(DPI, DPI))
            print(f"✅ Etiqueta gerada: {file_name}")
            imagens_pdf.append(img_final.convert("RGB"))
            total_imgs += 1

    pdf_path = None
    if imagens_pdf:
        pdf_path = output_dir / pdf_name
        imagens_pdf[0].save(pdf_path, save_all=True, append_images=imagens_pdf[1:])
        print(f"📄 PDF gerado: {pdf_path}")

    print(f"🎉 Concluído: {total_imgs} imagens em {output_dir}")
    return (len(registros), total_imgs, pdf_path)


def gerar_de_queryset(
    qs,
    output_dir: Path,
    json_dir: Path,
    base_url: str,
    empresa_endereco: str,
    empresa_tel: str,
    logo_path: Path,
    pdf_name: str = "labels.pdf",
    clean: bool = True,
    export_json: bool = True,
) -> Tuple[int, int, Optional[Path]]:
    registros = []
    for obj in qs:
        registros.append(
            {
                "id": obj.id,
                "truss_number": obj.truss_number,
                "job_number": obj.job_number,
                "tipo": obj.tipo,
                "quantidade": obj.quantidade,
                "ply": obj.ply,  # Será convertido em exportar_json
                "endereco": obj.endereco,
                "tamanho": obj.tamanho,
                "status": obj.status,
            }
        )

    if export_json:
        exportar_json(registros, json_dir)

    return gerar_imagens_e_pdf(
        registros,
        output_dir,
        logo_path,
        base_url,
        empresa_endereco,
        empresa_tel,
        pdf_name=pdf_name,
        clean=clean,
    )


def gerar_de_csv(
    csv_path: Path,
    output_dir: Path,
    json_dir: Path,
    base_url: str,
    empresa_endereco: str,
    empresa_tel: str,
    logo_path: Path,
    pdf_name: str = "labels.pdf",
    clean: bool = True,
    export_json: bool = True,
) -> Tuple[int, int, Optional[Path]]:
    if pd is None:
        raise RuntimeError("pandas não instalado – necessário para CSV.")
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {csv_path}")
    df = pd.read_csv(csv_path)

    registros = []
    for _, row in df.iterrows():
        try:
            tid = int(row["id"])
        except Exception:
            continue
        registros.append(
            {
                "id": tid,
                "truss_number": row.get("truss_number", ""),
                "job_number": row.get("job_number", ""),
                "tipo": row.get("tipo", ""),
                "quantidade": row.get("quantidade", ""),
                "ply": row.get("ply", ""),
                "endereco": row.get("endereco", ""),
                "tamanho": row.get("tamanho", ""),
                "status": row.get("status", ""),
            }
        )

    if export_json:
        exportar_json(registros, json_dir)

    return gerar_imagens_e_pdf(
        registros,
        output_dir,
        logo_path,
        base_url,
        empresa_endereco,
        empresa_tel,
        pdf_name=pdf_name,
        clean=clean,
    )