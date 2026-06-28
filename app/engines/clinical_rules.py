from pydantic import BaseModel, Field
from typing import Dict, Any, List, Literal

class VitalsInput(BaseModel):
    respiration_rate: int = Field(..., ge=1, le=100)
    oxygen_saturation: int = Field(..., ge=0, le=100)
    oxygen_saturation_scale: Literal["SCALE_1", "SCALE_2"] = "SCALE_1"
    supplemental_oxygen: bool
    systolic_blood_pressure: int = Field(..., ge=0, le=300)
    heart_rate: int = Field(..., ge=0, le=300)
    temperature: float = Field(..., ge=25.0, le=45.0)
    neurological_status: Literal["A", "V", "P", "U"] = "A"

class NEWS2Result(BaseModel):
    aggregate_score: int
    parameter_breakdown: Dict[str, int]
    has_red_flag: bool
    red_flag_triggers: List[str]
    clinical_risk_tier: Literal["MINIMAL", "LOW", "MEDIUM", "HIGH"]
    mandated_escalation: str
    version: str = "RCP-NEWS2-2017-v1"

class CertifiedNEWS2Engine:
    @staticmethod
    def compute(v: VitalsInput) -> NEWS2Result:
        breakdown: Dict[str, int] = {}
        red_flags: List[str] = []

        if v.respiration_rate <= 8 or v.respiration_rate >= 25:
            rr = 3
        elif 9 <= v.respiration_rate <= 11 or 22 <= v.respiration_rate <= 24:
            rr = 1
        elif 12 <= v.respiration_rate <= 20:
            rr = 0
        else:
            rr = 2
        breakdown["respiration_rate"] = rr
        if rr == 3:
            red_flags.append("RR critical: " + str(v.respiration_rate) + " bpm")

        if v.oxygen_saturation_scale == "SCALE_1":
            if v.oxygen_saturation <= 91: o2 = 3
            elif 92 <= v.oxygen_saturation <= 93: o2 = 2
            elif 94 <= v.oxygen_saturation <= 95: o2 = 1
            else: o2 = 0
        else:
            if v.oxygen_saturation <= 83 or (v.oxygen_saturation >= 97 and v.supplemental_oxygen): o2 = 3
            elif 84 <= v.oxygen_saturation <= 85 or 95 <= v.oxygen_saturation <= 96: o2 = 2
            elif 86 <= v.oxygen_saturation <= 87 or 93 <= v.oxygen_saturation <= 94: o2 = 1
            else: o2 = 0
        breakdown["oxygen_saturation"] = o2
        if o2 == 3:
            red_flags.append("SpO2 critical: " + str(v.oxygen_saturation) + "%")

        breakdown["supplemental_oxygen"] = 2 if v.supplemental_oxygen else 0

        sbp = v.systolic_blood_pressure
        if sbp <= 90 or sbp >= 220: bp = 3
        elif 91 <= sbp <= 100: bp = 2
        elif 101 <= sbp <= 110: bp = 1
        else: bp = 0
        breakdown["systolic_blood_pressure"] = bp
        if bp == 3:
            red_flags.append("BP critical: " + str(sbp) + " mmHg")

        hr = v.heart_rate
        if hr <= 40 or hr >= 131: h = 3
        elif 111 <= hr <= 130: h = 2
        elif 41 <= hr <= 50 or 91 <= hr <= 110: h = 1
        else: h = 0
        breakdown["heart_rate"] = h
        if h == 3:
            red_flags.append("HR critical: " + str(hr) + " bpm")

        t = v.temperature
        if t <= 35.0: ts = 3
        elif t >= 39.1: ts = 2
        elif 35.1 <= t <= 36.0 or 38.1 <= t <= 39.0: ts = 1
        else: ts = 0
        breakdown["temperature"] = ts
        if ts == 3:
            red_flags.append("Temp critical: " + str(t) + "C")

        avpu = 3 if v.neurological_status in ["V", "P", "U"] else 0
        breakdown["neurological_status"] = avpu
        if avpu == 3:
            red_flags.append("Neuro deterioration: AVPU=" + v.neurological_status)

        total = sum(breakdown.values())
        has_red = len(red_flags) > 0

        if has_red or total >= 7:
            risk = "HIGH"
            esc = "URGENT: Immediate emergency assessment. Consider ICU/HDU."
        elif 5 <= total <= 6:
            risk = "MEDIUM"
            esc = "MEDIUM: Urgent review within 1 hour."
        elif 1 <= total <= 4:
            risk = "LOW"
            esc = "LOW: Monitor every 4-6 hours."
        else:
            risk = "MINIMAL"
            esc = "ROUTINE: Standard 12-hourly monitoring."

        return NEWS2Result(
            aggregate_score=total,
            parameter_breakdown=breakdown,
            has_red_flag=has_red,
            red_flag_triggers=red_flags,
            clinical_risk_tier=risk,
            mandated_escalation=esc
        )
