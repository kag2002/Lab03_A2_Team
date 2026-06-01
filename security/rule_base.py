from __future__ import annotations

from dataclasses import dataclass, field
import copy
import re
from typing import Any


Severity = str

BLOCKING_SEVERITIES: set[Severity] = {"high", "critical"}
MAX_MESSAGE_LENGTH = 2_000
MAX_LIST_ITEMS = 12
MAX_TEXT_FIELD_LENGTH = 160
MAX_DURATION_DAYS = 90

ALLOWED_TOOLS = {
    "Grade_Search_Tool",
    "Score_Analyzer",
    "Learning_Gap_Detector",
    "Study_Plan_Generator",
    "Stop",
}

TOOL_SCHEMAS: dict[str, set[str]] = {
    "Grade_Search_Tool": {"student_id", "course_name"},
    "Score_Analyzer": {"scores"},
    "Learning_Gap_Detector": {"low_score_parts"},
    "Study_Plan_Generator": {"weak_topics", "duration"},
    "Stop": set(),
}

STUDENT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
COURSE_NAME_RE = re.compile(r"^[\w\s&()+/.,:'-]{1,80}$", re.UNICODE)
SKILL_NAME_RE = re.compile(r"^[\w\s&()+/.,:'-]{1,80}$", re.UNICODE)

SENSITIVE_KEY_RE = re.compile(
    r"(api[_-]?key|token|secret|password|credential|private[_-]?key)",
    re.IGNORECASE,
)

STUDENT_ID_IN_TEXT_RE = re.compile(
    r"\b(?:SV|STU|HS|HV|ID)[-_]?[A-Za-z0-9]{2,16}\b",
    re.IGNORECASE,
)

PROMPT_INJECTION_PATTERNS = [
    r"\bignore\s+(all\s+)?(previous|above)\s+(instructions?|messages?)\b",
    r"\bdisregard\s+(previous|above)\s+(instructions?|messages?)\b",
    r"\breveal\s+(the\s+)?(system|developer)\s+(prompt|message|instructions?)\b",
    r"\bshow\s+(me\s+)?(hidden|system|developer)\s+(prompt|instructions?)\b",
    r"\bjailbreak\b",
    r"\bbypass\s+(security|guardrails?|policy|rules?)\b",
    r"\bact\s+as\s+(developer|system|admin|root)\b",
    r"\btool\s+call\s+override\b",
    r"\bqu[eê]n\s+(h[eế]t|to[aà]n\s+b[oộ])\s+(ch[iỉ]\s+d[aẫ]n|l[eệ]nh)\b",
    r"\bb[oỏ]\s+qua\s+(ch[iỉ]\s+d[aẫ]n|lu[aậ]t|b[aả]o\s+m[aậ]t)\b",
    r"\bti[eế]t\s+l[oộ]\s+(system|prompt|api|key|token|\.env)\b",
]

ATTACK_PATTERNS = {
    "SEC_SQL_INJECTION": [
        r"(?i)\bunion\s+select\b",
        r"(?i)\bdrop\s+table\b",
        r"(?i)\binsert\s+into\b",
        r"(?i)\bdelete\s+from\b",
        r"(?i)\bor\s+['\"]?1['\"]?\s*=\s*['\"]?1\b",
        r"--|/\*|\*/",
        r"(?i)\bsleep\s*\(",
        r"(?i)\bxp_cmdshell\b",
    ],
    "SEC_XSS": [
        r"(?i)<\s*script\b",
        r"(?i)javascript\s*:",
        r"(?i)\bon(?:error|load|click)\s*=",
        r"(?i)data\s*:\s*text/html",
    ],
    "SEC_PATH_TRAVERSAL": [
        r"(\.\./|\.\.\\)",
        r"(?i)\bfile\s*:",
        r"(?i)\b/etc/passwd\b",
        r"(?i)\bC:\\Windows\\",
    ],
    "SEC_COMMAND_INJECTION": [
        r"(?i)(;|&&|\|\|)\s*(rm|del|erase|curl|wget|powershell|cmd|bash|sh)\b",
        r"(?i)\bInvoke-WebRequest\b",
        r"(?i)\bStart-Process\b",
    ],
    "SEC_SECRET_EXFILTRATION": [
        r"(?i)\bOPENAI_API_KEY\b",
        r"(?i)\bANTHROPIC_API_KEY\b",
        r"(?i)\bAI_LOG_API_KEY\b",
        r"(?i)\.env\b",
        r"(?i)\bapi\s*key\b",
    ],
}


@dataclass(frozen=True)
class SecurityFinding:
    rule_id: str
    severity: Severity
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SecurityDecision:
    allowed: bool
    findings: list[SecurityFinding] = field(default_factory=list)
    sanitized_input: str | None = None
    normalized_args: dict[str, Any] | None = None


@dataclass(frozen=True)
class SecurityContext:
    user_id: str
    student_id: str | None = None
    allowed_student_ids: frozenset[str] = field(default_factory=frozenset)
    role: str = "student"

    def can_access_student(self, requested_student_id: str) -> bool:
        if self.role in ("admin", "teacher") and not self.allowed_student_ids:
            return True

        allowed_ids = set(self.allowed_student_ids)
        if self.student_id:
            allowed_ids.add(self.student_id)

        return requested_student_id in allowed_ids


def validate_message(message: str, context: SecurityContext) -> SecurityDecision:
    findings: list[SecurityFinding] = []

    if not isinstance(message, str):
        return _blocked(
            "SEC_INPUT_TYPE",
            "high",
            "User message must be a string.",
        )

    sanitized = _strip_control_chars(message).strip()

    if not sanitized:
        findings.append(
            SecurityFinding("SEC_EMPTY_INPUT", "high", "User message is empty.")
        )

    if len(sanitized) > MAX_MESSAGE_LENGTH:
        findings.append(
            SecurityFinding(
                "SEC_INPUT_TOO_LONG",
                "high",
                f"User message is longer than {MAX_MESSAGE_LENGTH} characters.",
                {"length": len(sanitized)},
            )
        )

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, sanitized, re.IGNORECASE):
            findings.append(
                SecurityFinding(
                    "SEC_PROMPT_INJECTION",
                    "high",
                    "Message appears to contain prompt-injection instructions.",
                )
            )
            break

    findings.extend(_find_attack_patterns(sanitized))
    findings.extend(_find_unauthorized_student_ids(sanitized, context))

    return SecurityDecision(
        allowed=_is_allowed(findings),
        findings=findings,
        sanitized_input=sanitized,
    )


def validate_tool_call(
    tool_name: str,
    args: dict[str, Any] | None,
    context: SecurityContext,
) -> SecurityDecision:
    findings: list[SecurityFinding] = []

    if tool_name not in ALLOWED_TOOLS:
        return _blocked(
            "SEC_TOOL_NOT_ALLOWED",
            "critical",
            f"Tool '{tool_name}' is not in the allowed tool list.",
        )

    normalized_args = copy.deepcopy(args or {})
    expected_keys = TOOL_SCHEMAS[tool_name]
    actual_keys = set(normalized_args)

    missing_keys = expected_keys - actual_keys
    unexpected_keys = actual_keys - expected_keys

    if missing_keys:
        findings.append(
            SecurityFinding(
                "SEC_TOOL_ARGS_MISSING",
                "high",
                f"Tool '{tool_name}' is missing required arguments.",
                {"missing_keys": sorted(missing_keys)},
            )
        )

    if unexpected_keys:
        findings.append(
            SecurityFinding(
                "SEC_TOOL_ARGS_UNEXPECTED",
                "high",
                f"Tool '{tool_name}' received unexpected arguments.",
                {"unexpected_keys": sorted(unexpected_keys)},
            )
        )

    if tool_name == "Grade_Search_Tool":
        findings.extend(_validate_grade_search_args(normalized_args, context))
    elif tool_name == "Score_Analyzer":
        findings.extend(_validate_scores_arg(normalized_args.get("scores")))
    elif tool_name == "Learning_Gap_Detector":
        findings.extend(_validate_text_list_arg("low_score_parts", normalized_args))
    elif tool_name == "Study_Plan_Generator":
        findings.extend(_validate_text_list_arg("weak_topics", normalized_args))
        findings.extend(_validate_duration_arg(normalized_args.get("duration")))
    elif tool_name == "Stop" and normalized_args:
        findings.append(
            SecurityFinding(
                "SEC_STOP_ARGS",
                "high",
                "Stop tool must not receive arguments.",
            )
        )

    return SecurityDecision(
        allowed=_is_allowed(findings),
        findings=findings,
        normalized_args=normalized_args,
    )


def validate_tool_result(
    tool_name: str,
    result: dict[str, Any],
    context: SecurityContext,
) -> SecurityDecision:
    findings: list[SecurityFinding] = []

    if tool_name not in ALLOWED_TOOLS:
        return _blocked(
            "SEC_TOOL_RESULT_UNKNOWN",
            "critical",
            f"Cannot trust result from unknown tool '{tool_name}'.",
        )

    sanitized_result = redact_secrets(result)

    if sanitized_result != result:
        findings.append(
            SecurityFinding(
                "SEC_TOOL_RESULT_SECRET_REDACTED",
                "medium",
                "Sensitive-looking fields were redacted from tool result.",
            )
        )

    if tool_name == "Grade_Search_Tool":
        requested_student_id = sanitized_result.get("student_id")
        if isinstance(requested_student_id, str) and not context.can_access_student(
            requested_student_id
        ):
            findings.append(
                SecurityFinding(
                    "SEC_TOOL_RESULT_IDOR",
                    "critical",
                    "Grade result belongs to a student outside the caller scope.",
                    {"student_id": requested_student_id},
                )
            )

    return SecurityDecision(
        allowed=_is_allowed(findings),
        findings=findings,
        normalized_args=sanitized_result,
    )


def redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if SENSITIVE_KEY_RE.search(str(key)):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_secrets(item)
        return redacted

    if isinstance(value, list):
        return [redact_secrets(item) for item in value]

    if isinstance(value, str):
        return re.sub(
            r"\b(?:sk|sk-ant|ghp|xoxb)-[A-Za-z0-9_\-]{12,}\b",
            "[REDACTED]",
            value,
        )

    return value


def _blocked(rule_id: str, severity: Severity, message: str) -> SecurityDecision:
    return SecurityDecision(
        allowed=False,
        findings=[SecurityFinding(rule_id, severity, message)],
    )


def _is_allowed(findings: list[SecurityFinding]) -> bool:
    return not any(finding.severity in BLOCKING_SEVERITIES for finding in findings)


def _strip_control_chars(text: str) -> str:
    return "".join(
        char for char in text if char in "\n\r\t" or not unicodedata_category_is_control(char)
    )


def unicodedata_category_is_control(char: str) -> bool:
    return ord(char) < 32 or ord(char) == 127


def _find_attack_patterns(text: str) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    for rule_id, patterns in ATTACK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                findings.append(
                    SecurityFinding(
                        rule_id,
                        "high",
                        "Input matches a known external attack pattern.",
                    )
                )
                break
    return findings


def _find_unauthorized_student_ids(
    text: str,
    context: SecurityContext,
) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    for student_id in set(STUDENT_ID_IN_TEXT_RE.findall(text)):
        if not context.can_access_student(student_id):
            findings.append(
                SecurityFinding(
                    "SEC_STUDENT_SCOPE",
                    "critical",
                    "Message references a student id outside the caller scope.",
                    {"student_id": student_id},
                )
            )
    return findings


def _validate_grade_search_args(
    args: dict[str, Any],
    context: SecurityContext,
) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    student_id = args.get("student_id")
    course_name = args.get("course_name")

    if not isinstance(student_id, str) or not STUDENT_ID_RE.match(student_id):
        findings.append(
            SecurityFinding(
                "SEC_STUDENT_ID_FORMAT",
                "high",
                "student_id has an invalid format.",
            )
        )
    elif not context.can_access_student(student_id):
        findings.append(
            SecurityFinding(
                "SEC_TOOL_STUDENT_SCOPE",
                "critical",
                "Tool call tries to access a student outside the caller scope.",
                {"student_id": student_id},
            )
        )

    if not isinstance(course_name, str) or not COURSE_NAME_RE.match(course_name):
        findings.append(
            SecurityFinding(
                "SEC_COURSE_NAME_FORMAT",
                "high",
                "course_name has an invalid format.",
            )
        )

    if isinstance(course_name, str):
        findings.extend(_find_attack_patterns(course_name))

    return findings


def _validate_scores_arg(scores: Any) -> list[SecurityFinding]:
    if not isinstance(scores, dict) or not scores:
        return [
            SecurityFinding(
                "SEC_SCORES_FORMAT",
                "high",
                "scores must be a non-empty object.",
            )
        ]

    findings: list[SecurityFinding] = []
    if len(scores) > MAX_LIST_ITEMS:
        findings.append(
            SecurityFinding(
                "SEC_SCORES_TOO_MANY_FIELDS",
                "high",
                "scores contains too many fields.",
                {"field_count": len(scores)},
            )
        )

    for skill, score in scores.items():
        if not isinstance(skill, str) or not SKILL_NAME_RE.match(skill):
            findings.append(
                SecurityFinding(
                    "SEC_SCORE_SKILL_FORMAT",
                    "high",
                    "Score skill name has an invalid format.",
                    {"skill": str(skill)},
                )
            )
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            findings.append(
                SecurityFinding(
                    "SEC_SCORE_VALUE_FORMAT",
                    "high",
                    "Score value must be numeric.",
                    {"skill": str(skill)},
                )
            )
        elif score < 0 or score > 100:
            findings.append(
                SecurityFinding(
                    "SEC_SCORE_VALUE_RANGE",
                    "high",
                    "Score value must be between 0 and 100.",
                    {"skill": str(skill), "score": score},
                )
            )

    return findings


def _validate_text_list_arg(
    arg_name: str,
    args: dict[str, Any],
) -> list[SecurityFinding]:
    value = args.get(arg_name)
    if not isinstance(value, list) or not value:
        return [
            SecurityFinding(
                "SEC_TEXT_LIST_FORMAT",
                "high",
                f"{arg_name} must be a non-empty list.",
            )
        ]

    findings: list[SecurityFinding] = []
    if len(value) > MAX_LIST_ITEMS:
        findings.append(
            SecurityFinding(
                "SEC_TEXT_LIST_TOO_LONG",
                "high",
                f"{arg_name} contains too many items.",
                {"count": len(value)},
            )
        )

    for item in value:
        if not isinstance(item, str) or not item.strip():
            findings.append(
                SecurityFinding(
                    "SEC_TEXT_LIST_ITEM_FORMAT",
                    "high",
                    f"{arg_name} contains a non-text item.",
                )
            )
            continue

        if len(item) > MAX_TEXT_FIELD_LENGTH or not SKILL_NAME_RE.match(item):
            findings.append(
                SecurityFinding(
                    "SEC_TEXT_LIST_ITEM_UNSAFE",
                    "high",
                    f"{arg_name} contains an unsafe text item.",
                    {"item": item[:40]},
                )
            )
        findings.extend(_find_attack_patterns(item))

    return findings


def _validate_duration_arg(duration: Any) -> list[SecurityFinding]:
    if not isinstance(duration, str) or not duration.strip():
        return [
            SecurityFinding(
                "SEC_DURATION_FORMAT",
                "high",
                "duration must be a non-empty string.",
            )
        ]

    days = _duration_to_days(duration)
    if days is None:
        return [
            SecurityFinding(
                "SEC_DURATION_PARSE",
                "high",
                "duration must use days, weeks, or months.",
                {"duration": duration},
            )
        ]

    if days <= 0 or days > MAX_DURATION_DAYS:
        return [
            SecurityFinding(
                "SEC_DURATION_RANGE",
                "high",
                f"duration must be between 1 and {MAX_DURATION_DAYS} days.",
                {"duration": duration, "days": days},
            )
        ]

    return []


def _duration_to_days(duration: str) -> int | None:
    normalized = duration.strip().lower()
    match = re.match(r"^(\d{1,3})\s*(day|days|ng[aà]y)$", normalized)
    if match:
        return int(match.group(1))

    match = re.match(r"^(\d{1,2})\s*(week|weeks|tu[aầ]n)$", normalized)
    if match:
        return int(match.group(1)) * 7

    match = re.match(r"^(\d{1,2})\s*(month|months|th[aá]ng)$", normalized)
    if match:
        return int(match.group(1)) * 30

    return None
