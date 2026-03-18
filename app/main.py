from fastapi import FastAPI

from app.routers import notes, changes, search

app = FastAPI(title="Obsidian API", version="0.1.0")

app.include_router(notes.router)
app.include_router(changes.router)
app.include_router(search.router)


@app.get("/health")
def health():
    return {"status": "ok"}
