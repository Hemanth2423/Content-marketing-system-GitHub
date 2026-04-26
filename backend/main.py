import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

from config import settings
from api import briefs, pipeline, approvals, publish, audit, alerts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Index ChromaDB on startup
    print("Indexing company knowledge base...")
    try:
        from vector_store import get_store
        store = get_store()
        n = store.index_company_data()
        print(f"  → {n} new chunks indexed (0 = already up to date)")
    except Exception as e:
        print(f"  → ChromaDB indexing failed: {e}")

    # Start SLA monitoring scheduler
    print("Starting SLA monitor...")
    from alerts import get_alert_engine
    sla_scheduler = BackgroundScheduler(timezone="UTC")
    sla_scheduler.add_job(
        get_alert_engine().check_sla,
        "interval",
        seconds=5,
        id="sla_monitor",
    )
    sla_scheduler.start()

    # Initialize publish scheduler singleton
    from scheduler import get_scheduler
    get_scheduler()
    print("Publish scheduler ready.")
    print("Backend ready — http://localhost:8000")

    yield

    sla_scheduler.shutdown(wait=False)
    get_scheduler().shutdown()


app = FastAPI(
    title="GitHub Content Marketing System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(briefs.router)
app.include_router(pipeline.router)
app.include_router(approvals.router)
app.include_router(publish.router)
app.include_router(audit.router)
app.include_router(alerts.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
