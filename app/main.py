from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/trussesdb")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# Modelo
class Truss(Base):
    __tablename__ = "trusses"
    id = Column(Integer, primary_key=True, index=True)
    job_number = Column(String, nullable=False)
    truss_number = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependência de sessão
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/trusses/")
def create_truss(job_number: str, truss_number: str, db: Session = Depends(get_db)):
    db_truss = Truss(job_number=job_number, truss_number=truss_number)
    db.add(db_truss)
    db.commit()
    db.refresh(db_truss)
    return db_truss

@app.get("/trusses/{truss_id}")
def read_truss(truss_id: int, db: Session = Depends(get_db)):
    truss = db.query(Truss).filter(Truss.id == truss_id).first()
    if not truss:
        raise HTTPException(status_code=404, detail="Truss not found")
    return truss
