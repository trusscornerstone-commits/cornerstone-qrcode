import os
import psycopg2
from datetime import datetime
import fitz  # PyMuPDF
import cv2
import numpy as np
import re
import shutil
import logging
import random  # <--- adicionado para gerar números aleatórios
from colorama import Fore, Style, init
from zoneinfo import ZoneInfo  # Python 3.9+

init(autoreset=True)

# ---------------------- CONFIG ----------------------
BASE_DIR = r"C:\Users\FATEX\Documents\qrcodes"
BACKUP_DIR = os.path.join(BASE_DIR, "backup")
LOG_PATH = os.path.join(BASE_DIR, "logs\qrcode_import.log")

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

pdf_files = [f for f in os.listdir(BASE_DIR) if f.lower().endswith(".pdf")]
if not pdf_files:
    raise FileNotFoundError(f"Nenhum arquivo PDF encontrado em {BASE_DIR}")
PDF_PATH = os.path.join(BASE_DIR, pdf_files[0])
print(f"{Fore.CYAN}📄 PDF encontrado: {PDF_PATH}")
logging.info(f"PDF encontrado: {PDF_PATH}")

# ---------------------- DB CONFIG ----------------------
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'dbname': 'cornerstone',
    'user': 'cornerstone',
    'password': 'cornerstone'
}

# ---------------------- BANCO ----------------------
def ensure_table_and_constraints(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS qr_codeTrusses (
                id SERIAL PRIMARY KEY,
                truss_id VARCHAR(20),
                serial_number VARCHAR(150) UNIQUE,
                quantity INTEGER,
                span VARCHAR(50),
                produced BOOLEAN DEFAULT FALSE,
                production_date TIMESTAMP NULL,
                create_date TIMESTAMP,
                floor VARCHAR(50),
                project VARCHAR(50),
                table_number VARCHAR(50),
                update_date TIMESTAMP,
                producer_name VARCHAR(100),
                unit_number INTEGER
            );
        """)
    conn.commit()

def insert_unit_rows(conn, truss_id, quantity, span, floor, project, counters):
    """Cria uma linha por unidade, sorteando table_number de 1 a 4."""
    boston_tz = ZoneInfo("America/New_York")
    now = datetime.now(boston_tz).strftime("%Y-%m-%d %H:%M:%S")

    # 🔹 table_number aleatório entre 1 e 4
    table_number = 1#str(random.randint(1, 4))

    for unit_number in range(1, quantity + 1):
        serial_number = f"{truss_id}-{floor}-{span}-{unit_number}-of-{quantity}"
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO qr_codeTrusses (
                        truss_id, serial_number, quantity, span,
                        produced, production_date, create_date,
                        floor, project, table_number,
                        update_date, producer_name, unit_number
                    )
                    VALUES (%s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s)
                """, (
                    truss_id,
                    serial_number,
                    quantity,
                    span,
                    False,
                    None,
                    now,
                    floor,
                    project,
                    table_number,  # <--- aqui entra o número da mesa
                    now,
                    None,
                    unit_number
                ))
            conn.commit()
            print(f"{Fore.GREEN}✅ Inserido: {serial_number} (Mesa {table_number})")
            logging.info(f"Inserido: {serial_number} (Mesa {table_number})")
            counters["sucessos"] += 1
        except Exception as e:
            conn.rollback()
            msg = str(e).lower()
            if "duplicate key" in msg:
                print(f"{Fore.YELLOW}⚠️ Já existe: {serial_number}")
                logging.warning(f"Duplicado: {serial_number}")
                counters["duplicados"] += 1
            else:
                print(f"{Fore.RED}❌ Erro ao inserir {serial_number}: {e}")
                logging.error(f"Erro ao inserir {serial_number}: {e}")
                counters["erros"] += 1

# ---------------------- PARSE QR ----------------------
def parse_qr_data(text):
    text = " ".join(text.split())
    parts = text.split()

    truss_id = parts[0]

    total_qty = 1
    if "OF" in parts:
        try:
            total_qty = int(parts[parts.index("OF") + 1])
        except:
            pass

    span_match = re.search(r"\b\d{2}-\d{2}-\d{2}\b", text)
    span = span_match.group(0) if span_match else "unknown"

    floor = "N/A"
    if "BATCH:" in parts:
        i = parts.index("BATCH:") + 1
        if i < len(parts):
            floor = parts[i]

    project = "N/A"
    try:
        si = parts.index(span)
        if si + 1 < len(parts):
            project = parts[si + 1]
    except:
        pass

    return truss_id, total_qty, span, floor, project


# ---------------------- EXECUÇÃO ----------------------
print(f"{Fore.CYAN}🔄 Convertendo PDF em imagens com PyMuPDF...")
logging.info("Convertendo PDF em imagens...")

doc = fitz.open(PDF_PATH)
pages = []
for page in doc:
    pix = page.get_pixmap(dpi=300)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 1:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    pages.append(img)

conn = psycopg2.connect(**DB_CONFIG)
ensure_table_and_constraints(conn)

detector = cv2.QRCodeDetector()
processed_qrs = set()
counters = {"sucessos": 0, "duplicados": 0, "erros": 0, "paginas": 0}

for i, img in enumerate(pages):
    counters["paginas"] += 1
    print(f"{Fore.CYAN}📄 Processando página {i+1}/{len(pages)}...")
    retval, decoded_infos, points, _ = detector.detectAndDecodeMulti(img)

    if retval and decoded_infos:
        for qr_data in decoded_infos:
            qr_data = qr_data.strip()
            if not qr_data or qr_data in processed_qrs:
                continue

            processed_qrs.add(qr_data)
            print(f"{Fore.MAGENTA}📦 QR lido: {qr_data}")
            logging.info(f"QR lido: {qr_data}")

            try:
                truss_id, total_qty, span, floor, project = parse_qr_data(qr_data)
                insert_unit_rows(conn, truss_id, total_qty, span, floor, project, counters)
            except Exception as e:
                print(f"{Fore.RED}⚠️ Erro ao processar QR: {e}")
                logging.error(f"Erro ao processar QR: {e}")
            break  # Apenas 1 QR por página
    else:
        print(f"{Fore.YELLOW}⚠️ Nenhum QR Code detectado nesta página.")
        logging.warning(f"Nenhum QR Code detectado na página {i+1}.")

conn.close()

print(f"{Fore.GREEN}🏁 Processamento concluído!")
logging.info("Processamento concluído.")

# ---------------------- BACKUP E LIMPEZA ----------------------
os.makedirs(BACKUP_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_name = os.path.basename(PDF_PATH)
backup_path = os.path.join(BACKUP_DIR, backup_name)

try:
    shutil.move(PDF_PATH, backup_path)
    print(f"{Fore.CYAN}📦 PDF movido para backup: {backup_path}")
    logging.info(f"PDF movido para backup: {backup_path}")
except PermissionError as e:
    if e.winerror == 32:
        alt_backup_path = os.path.join(BACKUP_DIR, f"{timestamp}_{backup_name}")
        shutil.copy2(PDF_PATH, alt_backup_path)
        print(f"{Fore.YELLOW}⚠️ PDF estava aberto — criada cópia: {alt_backup_path}")
        logging.warning(f"PDF estava aberto — cópia criada: {alt_backup_path}")
        try:
            os.remove(PDF_PATH)
            print(f"{Fore.CYAN}🗑️ Original removido após cópia.")
        except Exception as e2:
            print(f"{Fore.RED}⚠️ Não foi possível remover o PDF original: {e2}")
            logging.error(f"Erro ao remover o PDF original: {e2}")
    else:
        print(f"{Fore.RED}⚠️ Erro ao mover PDF para backup: {e}")
        logging.error(f"Erro ao mover PDF: {e}")

# ---------------------- RESUMO ----------------------
print(Style.BRIGHT + Fore.CYAN + "\n===== RESUMO =====")
print(f"📄 Páginas processadas: {counters['paginas']}")
print(f"✅ Inserções: {counters['sucessos']}")
print(f"⚠️ Duplicados: {counters['duplicados']}")
print(f"❌ Erros: {counters['erros']}")
print(f"📜 Log salvo em: {LOG_PATH}")
logging.info(f"Resumo: {counters}")
