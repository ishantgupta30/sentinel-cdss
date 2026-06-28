import asyncio, logging
from typing import Any, Dict, List

logger = logging.getLogger("CDSS.Antigravity")

async def run_parallel_agents(tasks: List[Dict[str, Any]]) -> List[Any]:
    logger.info(f"Antigravity: running {len(tasks)} tasks in parallel")
    async def run_one(name, coro):
        result = await coro
        logger.info(f"Antigravity task '{name}' done")
        return result
    coroutines = [run_one(t["name"], t["coro"]) for t in tasks]
    results = await asyncio.gather(*coroutines, return_exceptions=True)
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error(f"Task '{tasks[i]['name']}' failed: {r}")
            results[i] = {"error": str(r)}
    return results

class AntigravityMCPParallelizer:
    def __init__(self, mcp_hub):
        self.mcp = mcp_hub

    async def fetch_all_parallel(self, patient_id: str, db) -> Dict[str, Any]:
        tasks = [
            {"name": "labs",    "coro": self.mcp.fetch_lab_data(patient_id)},
            {"name": "beds",    "coro": self.mcp.check_bed_inventory()},
            {"name": "history", "coro": self.mcp.retrieve_patient_history(patient_id, "allergies", db)},
        ]
        results = await run_parallel_agents(tasks)
        return {"labs": results[0], "beds": results[1],
                "patient_history": results[2], "fetched_with": "antigravity_parallel"}
