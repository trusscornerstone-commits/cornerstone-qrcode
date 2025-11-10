import os
import re
import psycopg2
from datetime import datetime
import fitz  # PyMuPDF
import cv2  # OpenCV
import numpy as np
from zoneinfo import ZoneInfo  # Python 3.9+

# CONFIGURAÇÕES
PDF_PATH = r"C:\Users\FATEX\Documents\qrcodes\(250015) Truss Tags.Pdf"
DB_CONFIG = {
    'host': 'localhost',  # se rodar fora do docker, use 'localhost'
    'port': '5432',
    'dbname': 'cornerstone',
    'user': 'cornerstone',
    'password': 'cornerstone'
}

# -------------------------------------------------------------------
# 🧱 Criar tabela caso não exista
# -------------------------------------------------------------------
def create_table_if_not_exists(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS qr_codeTrusses (
                id SERIAL PRIMARY KEY,
                truss_id VARCHAR(20),
                serial_number VARCHAR(50),
                quantity VARCHAR(20),
                span VARCHAR(50),
                produced BOOLEAN DEFAULT FALSE,
                production_date TIMESTAMP NULL,
                create_date TIMESTAMP,
                floor VARCHAR(50),
                project VARCHAR(50),
                table_number VARCHAR(50),
                update_date TIMESTAMP,
                producer_name VARCHAR(100)
            );
        """)
    conn.commit()

# -------------------------------------------------------------------
# 💾 Inserir dados
# -------------------------------------------------------------------
def insert_data(conn, truss_id, serial_number, quantity, span, floor, project):
    boston_tz = ZoneInfo("America/New_York")
    boston_now = datetime.now(boston_tz)
    formatted_datetime = boston_now.strftime("%Y-%m-%d %H:%M")

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO qr_codeTrusses (
                truss_id, serial_number, quantity, span, produced,
                production_date, create_date, floor, project,
                table_number, update_date, producer_name
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s
            );
        """, (
            truss_id,
            serial_number,
            quantity,
            span,
            False,
            None,
            formatted_datetime,
            floor,
            project,
            None,
            formatted_datetime,
            None
        ))
    conn.commit()

# -------------------------------------------------------------------
# 🧩 Processar string QR
# -------------------------------------------------------------------
def parse_qr_data(text):
    # Remove quebras de linha e espaços extras
    text = " ".join(text.split())
    parts = text.split()

    truss_id = parts[0]

    if "QTY:" in parts:
        qty_index = parts.index("QTY:") + 1
        # Pegando quantidade, se houver
        quantity = parts[qty_index] if qty_index < len(parts) else "N/A"
    else:
        quantity = "N/A"

    # Tentando pegar span e project de forma segura
    span = parts[qty_index + 1] if qty_index + 1 < len(parts) else "N/A"
    project = parts[qty_index + 2] if qty_index + 2 < len(parts) else "N/A"
    floor = parts[-1].split(":")[-1] if parts else "N/A"

    serial_number = f"{truss_id}-{floor}-{quantity}-{project}"
    return truss_id, serial_number, quantity, span, floor, project

# -------------------------------------------------------------------
# 🚀 Execução principal
# -------------------------------------------------------------------
print("🔄 Convertendo PDF em imagens com PyMuPDF...")

# Abrir PDF
doc = fitz.open(PDF_PATH)
pages = []
for page in doc:
    pix = page.get_pixmap(dpi=300)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:  # RGBA -> BGR
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 1:  # Grayscale -> BGR
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    pages.append(img)

# Conectar ao banco
conn = psycopg2.connect(**DB_CONFIG)

# Criar tabela se necessário
create_table_if_not_exists(conn)

# Inicializar detector OpenCV
detector = cv2.QRCodeDetector()

# Processar páginas
for i, img in enumerate(pages):
    print(f"📄 Processando página {i+1}/{len(pages)}...")

    # Detectar e decodificar múltiplos QR Codes
    retval, decoded_infos, points, _ = detector.detectAndDecodeMulti(img)

    if retval:
        for qr_data in decoded_infos:
            qr_data = qr_data.strip()
            if not qr_data:
                continue
            print(f"📦 QR lido: {qr_data}")
            try:
                truss_id, serial_number, quantity, span, floor, project = parse_qr_data(qr_data)
                insert_data(conn, truss_id, serial_number, quantity, span, floor, project)
                print(f"✅ Inserido: {truss_id}, {serial_number}, {quantity}, {span}, {floor}, {project}")
            except Exception as e:
                print(f"⚠️ Erro ao processar: {qr_data} -> {e}")
    else:
        print("⚠️ Nenhum QR Code detectado nesta página.")

conn.close()
print("🏁 Finalizado com sucesso!")
