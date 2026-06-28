from pydantic import BaseModel, Field
from typing import List, Literal

class ClinicalPerspective(BaseModel):
    recommended_ward: str
    severity_score: float = Field(..., ge=0.0, le=1.0)
    clinical_rationale: str
    is_converged: bool

class LogisticsPerspective(BaseModel):
    recommended_ward: str
    allocated_bed_id: str
    logistics_rationale: str
    is_converged: bool

class CompliancePerspective(BaseModel):
    is_approved: bool
    compliance_rationale: str
    unresolved_concerns: List[str] = []

class DebateCalibration(BaseModel):
    contradictions_detected: bool
    evidence_coverage_score: float = Field(..., ge=0.0, le=1.0)
    uncertainty_index: float = Field(..., ge=0.0, le=1.0)
    should_terminate_debate: bool
    termination_reason: str

class FinalAdjudication(BaseModel):
    final_ward_assignment: str
    allocated_bed_id: str
    medical_justification: str
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"]
    reasoning_chain: List[str]
    requires_critical_care: bool
