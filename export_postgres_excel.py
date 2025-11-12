import pandas as pd
from sqlalchemy import create_engine

# Configurações de conexão com o PostgreSQL no Docker
user = "cornerstone"
password = "cornerstone"   # senha definida no docker-compose
host = "localhost"          # se estiver acessando do host (fora do container)
port = "5432"               # porta padrão do PostgreSQL
database = "cornerstone"

# Cria o engine de conexão (via SQLAlchemy)
engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{database}")

# Nome da tabela a exportar
tabela = "qr_codetrusses"

# Lê os dados do banco
print(f"Lendo tabela '{tabela}' do banco '{database}'...")
df = pd.read_sql(f"SELECT * FROM {tabela}", engine)

# Exporta para Excel
arquivo_saida = f"{tabela}.xlsx"
df.to_excel(arquivo_saida, index=False)

print(f"✅ Exportação concluída: {arquivo_saida}")
