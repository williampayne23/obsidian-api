from fastapi import FastAPI

from app.routers import notes, changes, search, diagnostics

app = FastAPI(title="Obsidian API", version="0.1.0")

app.include_router(notes.router)
app.include_router(changes.router)
app.include_router(search.router)
app.include_router(diagnostics.router)


@app.get("/health")
def health():
    return {"status": "ok"}
