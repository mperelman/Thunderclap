"""Minimal test server to verify FastAPI works"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Thunderclap AI Server Running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/test")
async def test(data: dict):
    return {"received": data.get("message", "nothing")}

if __name__ == "__main__":
    import uvicorn
    print("Starting test server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)


