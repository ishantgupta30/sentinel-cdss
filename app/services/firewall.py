import logging, re
from fastapi import HTTPException

logger = logging.getLogger("CDSS.Firewall")
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous|prior|all)\s+instructions?", re.IGNORECASE),
    re.compile(r"system\s*(prompt)?\s*override", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"disregard\s+(your|all|the)\s+rules?", re.IGNORECASE),
]
PHI_PATTERNS = {
    "SSN": (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED-SSN]"),
    "EMAIL": (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED-EMAIL]"),
    "PHONE": (re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b"), "[REDACTED-PHONE]"),
}

class SecurityFirewall:
    @staticmethod
    def scrub_phi(text: str) -> str:
        for label, (pattern, replacement) in PHI_PATTERNS.items():
            text = pattern.sub(replacement, text)
        return text

    @staticmethod
    def check_injection(text: str) -> None:
        for pattern in INJECTION_PATTERNS:
            if pattern.search(text):
                raise HTTPException(status_code=400, detail="Security violation: adversarial content detected.")

    @classmethod
    def process_narrative(cls, raw_text: str) -> str:
        if len(raw_text) > 5000:
            raise HTTPException(status_code=400, detail="Input too long.")
        cls.check_injection(raw_text)
        return cls.scrub_phi(raw_text)
