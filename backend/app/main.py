import asyncio
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from app.config import get_settings  # noqa: E402
from app.routers.gmail import router as gmail_router  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


async def _scheduled_sync(stop: asyncio.Event, minutes: int) -> None:
    from app.gmail.sync import sync_all

    while not stop.is_set():
        try:
            await asyncio.to_thread(sync_all, get_settings())
        except Exception:
            logger.exception("scheduled gmail sync failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=minutes * 60)
        except asyncio.TimeoutError:
            continue


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Phase 2 routers (apply agent, referral outreach) mount alongside gmail_router.
    settings = get_settings()
    stop = asyncio.Event()
    task = None
    if settings.sync_interval_minutes > 0:
        task = asyncio.create_task(_scheduled_sync(stop, settings.sync_interval_minutes))
        logger.info("in-process gmail sync every %s minutes", settings.sync_interval_minutes)
    yield
    stop.set()
    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="JobMap Ingestion", lifespan=lifespan)
app.include_router(gmail_router)


@app.get("/health")
def health():
    return {"ok": True, "service": "jobmap-ingestion"}
