from fastapi import FastAPI

app = FastAPI(title="Pokemon Decision Engine API")

@app.get("/health")
def health():
    return {"status": "ok"}
@app.get("/")
def root():
    return {"message": "Pokemon Decision Engine API. Go to /docs"}

