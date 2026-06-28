import json, logging, time
from typing import Any, Callable, Coroutine, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.schemas import ClinicalPerspective, LogisticsPerspective, CompliancePerspective, DebateCalibration, FinalAdjudication
from app.engines.clinical_rules import NEWS2Result, VitalsInput
from app.engines.gemini_async import async_gemini
from app.mcp.client import MCPToolHub

logger = logging.getLogger("CDSS.Orchestrator")

class DebateState:
    def __init__(self):
        self.round = 0
        self.history: List[Dict[str, Any]] = []
        self.converged = False

    def add_turn(self, agent: str, output: Any):
        self.history.append({"round": self.round, "agent": agent,
                             "output": output.model_dump() if hasattr(output, "model_dump") else output})

    def to_context(self) -> str:
        return json.dumps(self.history[-6:], indent=2, default=str)

class MultiAgentOrchestrator:
    MAX_DEBATE_ROUNDS = 2

    def __init__(self):
        self.mcp = MCPToolHub()

    async def run(self, patient_id: str, intake: str, vitals: VitalsInput,
                  news2: NEWS2Result, db: AsyncSession, progress_cb: Callable) -> Dict[str, Any]:
        start = time.perf_counter()
        await progress_cb("Phase 1: Querying MCP tools...")
        labs = await self.mcp.fetch_lab_data(patient_id)
        beds = await self.mcp.check_bed_inventory()
        history = await self.mcp.retrieve_patient_history(patient_id, "allergies", db)

        case_file = {
            "patient_id": patient_id, "intake": intake,
            "vitals": vitals.model_dump(),
            "IMMUTABLE_NEWS2_SCORE": news2.aggregate_score,
            "IMMUTABLE_RISK_TIER": news2.clinical_risk_tier,
            "IMMUTABLE_RED_FLAGS": news2.red_flag_triggers,
            "IMMUTABLE_ESCALATION": news2.mandated_escalation,
            "labs": labs, "beds": beds, "patient_history": history,
        }
        case_str = json.dumps(case_file, indent=2)
        debate = DebateState()

        await progress_cb("Phase 2: Multi-agent debate starting...")
        while debate.round < self.MAX_DEBATE_ROUNDS and not debate.converged:
            debate.round += 1
            await progress_cb(f"  Debate Round {debate.round}...")

            clinical = await async_gemini.generate_structured(
                "You are a Clinical Director. Recommend ward based on NEWS2. Score is IMMUTABLE. Output JSON.",
                f"CASE:\n{case_str}\nHISTORY:\n{debate.to_context()}", ClinicalPerspective)
            debate.add_turn("ClinicalExpert", clinical)

            logistics = await async_gemini.generate_structured(
                "You are a Logistics Manager. Find feasible bed. Never downgrade HIGH-risk patient. Output JSON.",
                f"CASE:\n{case_str}\nHISTORY:\n{debate.to_context()}", LogisticsPerspective)
            debate.add_turn("LogisticsPlanner", logistics)

            compliance = await async_gemini.generate_structured(
                "You are a Compliance Officer. Check plan safety. Output JSON.",
                f"CASE:\n{case_str}\nHISTORY:\n{debate.to_context()}", CompliancePerspective)
            debate.add_turn("ComplianceOfficer", compliance)

            calibration = await async_gemini.generate_structured(
                "You are an Audit Judge. Evaluate debate. Prevent groupthink. Output JSON.",
                f"NEWS2={news2.aggregate_score} RISK={news2.clinical_risk_tier}\nDEBATE:\n{debate.to_context()}",
                DebateCalibration)
            debate.add_turn("AuditJudge", calibration)

            if calibration.should_terminate_debate:
                debate.converged = True
                await progress_cb(f"  Converged: {calibration.termination_reason}")

        await progress_cb("Phase 3: Final adjudication...")
        final = await async_gemini.generate_structured(
            "You are the Lead Clinical Arbiter. Synthesize debate into final recommendation. NEWS2 is law. Output JSON.",
            f"CASE:\n{case_str}\nDEBATE:\n{debate.to_context()}", FinalAdjudication)

        if (news2.has_red_flag or news2.aggregate_score >= 7) and not final.requires_critical_care:
            logger.error("SAFETY GATE: Forcing requires_critical_care=True")
            final = FinalAdjudication(**{**final.model_dump(), "requires_critical_care": True})

        return {"case_file": case_file, "debate_trace": debate.history,
                "debate_rounds": debate.round, "converged": debate.converged,
                "final_adjudication": final.model_dump(),
                "latency_seconds": round(time.perf_counter() - start, 3)}

orchestrator = MultiAgentOrchestrator()
