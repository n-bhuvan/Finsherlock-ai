"""RingGuard AI — Stage 16: Layered Prompt Injection Defense & Security Sanitization.

Enforces a defense-in-depth architecture against prompt injection:
1. Untrusted-data boundary (<UNTRUSTED_DATA> delimiters wrapping all dynamic transaction/evidence content)
2. System instructions (immutable system boundary framing model task)
3. Input scanning (pre-execution regex heuristic detection of known injection patterns)
4. Structured schemas (strict Pydantic schema validation preventing arbitrary model output)
5. Claim grounding (mandatory evidence mapping rejecting ungrounded or fabricated claims)
6. Output sanitization (neutralizing XSS, script tags, and accidental secret leakage)
7. Deterministic fallback (safe zero-network rule-based fallback on any anomaly or detection)

Note: Pattern scanning is a heuristic first-line filter; complete protection is provided by
the layered defense-in-depth architecture rather than regex alone.
"""

import re
from typing import Tuple, List, Dict, Any

# Adversarial injection patterns (exact and regex variants)
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(the\s+)?(system|initial)\s+prompt",
    r"you\s+are\s+now\s+(a|an)?\s*",
    r"system\s*:",
    r"assistant\s*:",
    r"<\s*script\s*>",
    r"override\s+(the\s+)?(risk|score|decision|threshold)",
    r"grant\s+(admin|permission|access|authorization)",
    r"approve\s+(this\s+)?(payment|transaction|transfer)",
    r"freeze\s+account",
    r"reveal\s+(the\s+)?(api\s*key|secret|password|credential|system\s*prompt)",
    r"print\s+(the\s+)?(system\s*prompt|instructions)",
    r"bypass\s+(safety|security|verification)",
    r"simulate\s+(admin|root|system)",
]

COMPILED_INJECTION_REGEX = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

# Secret patterns to redact
SECRET_PATTERNS = [
    (re.compile(r"(?i)(api[_-]?key|secret|token|password|auth|bearer)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"), r"\1=[REDACTED]"),
    (re.compile(r"postgres(ql)?://[^:]+:[^@]+@[^/]+/[^\s]+"), "postgresql://[REDACTED_USER]:[REDACTED_PASS]@[REDACTED_HOST]/[REDACTED_DB]"),
    (re.compile(r"(?i)(sk-[a-zA-Z0-9]{20,}|AIzaSy[a-zA-Z0-9_\-]{33})"), "[REDACTED_API_KEY]"),
    (re.compile(r"(?i)(bearer\s+[a-zA-Z0-9_\-\.]{15,})"), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"), "[REDACTED_CARD_NUMBER]"),
]


class SecuritySanitizer:
    """Security engine for data minimization, prompt-injection defense, and output sanitization."""

    @staticmethod
    def scan_for_prompt_injection(text: str) -> Tuple[bool, List[str]]:
        """Scan input string for adversarial prompt injection patterns.
        
        Returns:
            (is_injection_detected, list_of_detected_patterns)
        """
        if not text:
            return False, []

        detected = []
        for regex in COMPILED_INJECTION_REGEX:
            matches = regex.findall(text)
            if matches:
                detected.append(regex.pattern)

        # Delimiter tampering check
        if "</UNTRUSTED_DATA>" in text or "<UNTRUSTED_DATA>" in text:
            detected.append("delimiter_injection_attempt")

        return len(detected) > 0, detected

    @staticmethod
    def minimize_data(text: str) -> str:
        """Apply data minimization: mask secrets and credentials, but preserve synthetic entity IDs.
        
        Synthetic IDs (ACC_000213, DEV_000045, EV_0042, TXN_00000203) are preserved for traceability.
        """
        if not text:
            return ""

        sanitized = text
        for pattern, replacement in SECRET_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)

        return sanitized

    @staticmethod
    def wrap_untrusted_data(data_content: str, label: str = "UNTRUSTED_DATA") -> str:
        """Enclose raw database or external content in explicit untrusted boundaries."""
        # Clean any accidental delimiter injection inside data_content
        cleaned = data_content.replace("<UNTRUSTED_DATA>", "[UNTRUSTED_TAG]").replace("</UNTRUSTED_DATA>", "[/UNTRUSTED_TAG]")
        return f"<{label}>\n{cleaned}\n</{label}>"

    @staticmethod
    def sanitize_output(text: str) -> str:
        """Sanitize LLM output text to prevent XSS, script injection, and leaked secrets."""
        if not text:
            return ""

        sanitized = text
        # Strip script tags
        sanitized = re.sub(r"(?i)<\s*script[^>]*>.*?<\s*/\s*script\s*>", "[SCRIPTS_STRIPPED]", sanitized, flags=re.DOTALL)
        sanitized = re.sub(r"(?i)<\s*script[^>]*>", "", sanitized)
        # Redact any accidental secret echoes
        for pattern, replacement in SECRET_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)

        return sanitized
