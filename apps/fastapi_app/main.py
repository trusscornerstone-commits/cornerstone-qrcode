from fastapi import FastAPI

app = FastAPI()

@app.get("/api/")
def api_root():
    return {"message": "API root is working!"}