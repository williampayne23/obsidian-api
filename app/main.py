import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.routers import notes, changes, search, diagnostics, reindex, webhooks
from app.services.watcher import watch_vault


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(watch_vault(settings.vault_path))
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Obsidian API", version="0.1.0", lifespan=lifespan)

app.include_router(notes.router)
app.include_router(changes.router)
app.include_router(search.router)
app.include_router(diagnostics.router)
app.include_router(reindex.router)
app.include_router(webhooks.router)


@app.get("/health")
def health():
    return {"status": "ok"}
