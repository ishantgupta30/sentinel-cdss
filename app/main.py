import asyncio, json, logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, create_tables
from app.engines.clinical_rules import CertifiedNEWS2Engine, VitalsInput
from app.services.firewall import SecurityFirewall
from app.agents.orchestrator import orchestrator

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield

app = FastAPI(title="Sentinel-CDSS", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "healthy", "system": "Sentinel-CDSS"}

@app.post("/api/v1/triage/stream")
async def triage_stream(
    patient_id: str = Form(...),
    intake_narrative: str = Form(...),
    respiration_rate: int = Form(...),
    oxygen_saturation: int = Form(...),
    oxygen_saturation_scale: str = Form(default="SCALE_1"),
    supplemental_oxygen: bool = Form(...),
    systolic_blood_pressure: int = Form(...),
    heart_rate: int = Form(...),
    temperature: float = Form(...),
    neurological_status: str = Form(default="A"),
    db: AsyncSession = Depends(get_db),
):
    clean = SecurityFirewall.process_narrative(intake_narrative)
    vitals = VitalsInput(
        respiration_rate=respiration_rate, oxygen_saturation=oxygen_saturation,
        oxygen_saturation_scale=oxygen_saturation_scale, supplemental_oxygen=supplemental_oxygen,
        systolic_blood_pressure=systolic_blood_pressure, heart_rate=heart_rate,
        temperature=temperature, neurological_status=neurological_status,
    )
    news2 = CertifiedNEWS2Engine.compute(vitals)

    async def stream():
        queue = asyncio.Queue()
        async def cb(msg): await queue.put(msg)
        task = asyncio.create_task(orchestrator.run(patient_id, clean, vitals, news2, db, cb))
        while not task.done() or not queue.empty():
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=0.1)
                yield f"data: {json.dumps({'update': msg})}\n\n"
            except asyncio.TimeoutError:
                continue
        result = task.result()
        yield f"data: {json.dumps({'complete': result, 'news2': news2.model_dump()})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
