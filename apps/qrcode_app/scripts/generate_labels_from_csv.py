#!/usr/bin/env python
"""
Uso rápido (fora do Django), lendo CSV:
  python apps/qrcode_app/scripts/generate_labels_from_csv.py --csv apps/qrcode_app/trusses.csv
"""
import argparse
import os
from pathlib import Path

from apps.qrcode_app.services.labels import gerar_de_csv

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--output-dir", default="apps/qrcode_app/templates/qrcodes")
    parser.add_argument("--json-dir", default="apps/qrcode_app/static/truss-data")
    parser.add_argument("--logo-path", default="cornerstone_logo.png")
    parser.add_argument("--web-base-url", default=os.getenv("WEB_BASE_URL", "https://cornerstone-app.onrender.com/truss"))
    parser.add_argument("--empresa-endereco", default="Rua Exemplo, 123 - Cidade/UF")
    parser.add_argument("--empresa-tel", default="(11) 99999-8888")
    parser.add_argument("--pdf-name", default="labels.pdf")
    parser.add_argument("--no-json", action="store_true")
    parser.add_argument("--no-clean", action="store_true")
    args = parser.parse_args()

    base = Path(".").resolve()
    gerar_de_csv(
        csv_path=base / args.csv,
        output_dir=base / args.output_dir,
        json_dir=base / args.json_dir,
        base_url=args.web_base_url,
        empresa_endereco=args.empresa_endereco,
        empresa_tel=args.empresa_tel,
        logo_path=base / args.logo_path,
        pdf_name=args.pdf_name,
        clean=not args.no_clean,
        export_json=not args.no_json,
    )

if __name__ == "__main__":
    main()