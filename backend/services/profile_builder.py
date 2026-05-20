import re
from typing import Dict, List, Tuple

from backend.observability.langsmith import traceable


ROLE_SKILLS: Dict[str, Dict[str, List[str]]] = {
    "Frontend Developer": {
        "JavaScript": ["javascript", "js", "ecmascript"],
        "TypeScript": ["typescript", "ts"],
        "React": ["react", "next.js", "nextjs"],
        "State Management": ["redux", "zustand", "mobx", "context api"],
        "HTML/CSS": ["html", "css", "scss", "sass", "tailwind"],
        "Testing": ["jest", "vitest", "cypress", "playwright", "rtl", "react testing library"],
        "API Integration": ["rest", "graphql", "axios", "fetch api"],
        "Performance": ["performance", "lighthouse", "web vitals", "optimization"],
        "Browser Fundamentals": ["event loop", "rendering", "browser", "dom"],
    },
    "Java Backend Developer": {
        "Java": ["java", "jdk", "jvm"],
        "Spring": ["spring", "spring boot", "spring mvc", "spring data"],
        "SQL": ["sql", "postgresql", "mysql", "oracle", "index", "query"],
        "REST APIs": ["rest", "rest api", "http", "json"],
        "Concurrency": ["multithreading", "thread", "concurrency", "executor", "synchronization"],
        "Transactions": ["transaction", "acidity", "isolation", "consistency"],
        "Caching": ["redis", "cache", "caching"],
        "Messaging": ["kafka", "rabbitmq", "queue", "messaging"],
        "Testing": ["junit", "mockito", "integration test", "testcontainers"],
    },
}

BASELINE_TOPICS: Dict[str, List[str]] = {
    "Frontend Developer": [
        "JavaScript fundamentals",
        "TypeScript typing and narrowing",
        "Browser rendering and event loop",
        "React component model",
        "API integration and async flows",
        "Testing fundamentals",
        "Resume-based project deep dive",
    ],
    "Java Backend Developer": [
        "Core Java and collections",
        "Spring Boot basics",
        "REST API design",
        "SQL and indexing basics",
        "Transactions and data consistency",
        "Concurrency and multithreading basics",
        "Resume-based project deep dive",
    ],
}


@traceable(run_type="chain", name="build_intake_artifacts")
def build_intake_artifacts(
    session: Dict[str, object],
    resume_parse: Dict[str, object],
    vacancy_parse: Dict[str, object],
) -> Dict[str, object]:
    role = str(session["role"])
    seniority = str(session["seniority"])
    interview_type = str(session["interview_type"])

    resume_text = str(resume_parse.get("normalized_text", ""))
    vacancy_text = str(vacancy_parse.get("normalized_text", ""))

    candidate_profile = build_candidate_profile(resume_text, role, seniority)
    job_profile = build_job_profile(vacancy_text, role, seniority)
    skill_gap_map = build_skill_gap_map(candidate_profile, job_profile)
    interview_topics = build_interview_topics(
        role=role,
        seniority=seniority,
        interview_type=interview_type,
        candidate_profile=candidate_profile,
        job_profile=job_profile,
        skill_gap_map=skill_gap_map,
    )

    return {
        "parser_summary": {
            "resume": parser_summary(resume_parse),
            "vacancy": parser_summary(vacancy_parse),
        },
        "candidate_profile": candidate_profile,
        "job_profile": job_profile,
        "skill_gap_map": skill_gap_map,
        "interview_topics": interview_topics,
    }


def parser_summary(parse_result: Dict[str, object]) -> Dict[str, object]:
    return {
        "source_type": parse_result.get("source_type", "unknown"),
        "parser_used": parse_result.get("parser_used", "unknown"),
        "char_count": parse_result.get("char_count", 0),
        "warnings": parse_result.get("warnings", []),
        "preview": str(parse_result.get("normalized_text", ""))[:280],
    }


def build_candidate_profile(resume_text: str, role: str, seniority: str) -> Dict[str, object]:
    skills = extract_skills(resume_text, role)
    projects = extract_project_highlights(resume_text)
    experience_years = extract_experience_years(resume_text)
    signals = detect_seniority_signals(resume_text)

    return {
        "target_role": role,
        "target_seniority": seniority,
        "experience_years_estimate": experience_years,
        "primary_skills": skills[:8],
        "project_highlights": projects[:4],
        "strengths": infer_strengths(skills, projects),
        "risk_signals": infer_candidate_risks(role, skills, projects),
        "seniority_signals": signals,
        "source_summary": summarize_text_density(resume_text),
    }


def build_job_profile(vacancy_text: str, role: str, seniority: str) -> Dict[str, object]:
    required_skills = extract_skills(vacancy_text, role)
    responsibilities = extract_responsibilities(vacancy_text)
    domain_keywords = extract_domain_keywords(vacancy_text)

    must_have = required_skills[:8]
    nice_to_have = [skill for skill in domain_keywords if skill not in must_have][:5]

    return {
        "target_role": role,
        "target_seniority": seniority,
        "required_skills": must_have,
        "preferred_skills": nice_to_have,
        "responsibilities": responsibilities[:6],
        "domain_keywords": domain_keywords[:10],
        "source_summary": summarize_text_density(vacancy_text),
    }


def build_skill_gap_map(
    candidate_profile: Dict[str, object],
    job_profile: Dict[str, object],
) -> Dict[str, object]:
    candidate_skills = set(candidate_profile.get("primary_skills", []))
    required_skills = list(job_profile.get("required_skills", []))
    preferred_skills = list(job_profile.get("preferred_skills", []))

    matched = [skill for skill in required_skills if skill in candidate_skills]
    missing = [skill for skill in required_skills if skill not in candidate_skills]
    partial = [skill for skill in preferred_skills if skill in candidate_skills]

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "adjacent_skills": partial,
        "risk_level": infer_risk_level(len(missing), len(required_skills)),
        "recommended_focus": missing[:4] or required_skills[:3],
    }


def build_interview_topics(
    role: str,
    seniority: str,
    interview_type: str,
    candidate_profile: Dict[str, object],
    job_profile: Dict[str, object],
    skill_gap_map: Dict[str, object],
) -> List[Dict[str, object]]:
    base_topics = BASELINE_TOPICS.get(role, [])
    missing = list(skill_gap_map.get("missing_skills", []))
    required = list(job_profile.get("required_skills", []))
    projects = list(candidate_profile.get("project_highlights", []))

    topic_names: List[str] = []
    for skill in missing + required:
        mapped = map_skill_to_topic(role, skill)
        if mapped and mapped not in topic_names:
            topic_names.append(mapped)

    for baseline in base_topics:
        if baseline not in topic_names:
            topic_names.append(baseline)

    topics: List[Dict[str, object]] = []
    for index, topic in enumerate(topic_names[:6]):
        priority = "high" if index < max(2, len(missing)) else "medium"
        reason = build_topic_reason(topic, missing, projects)
        topics.append(
            {
                "topic": topic,
                "priority": priority,
                "expected_difficulty": seniority.lower(),
                "interview_type": interview_type,
                "reason": reason,
            }
        )

    return topics


def extract_skills(text: str, role: str) -> List[str]:
    lowered = text.lower()
    found: List[str] = []
    for skill, aliases in ROLE_SKILLS.get(role, {}).items():
        if any(alias in lowered for alias in aliases):
            found.append(skill)
    return found


def extract_project_highlights(text: str) -> List[str]:
    candidates = split_lines(text)
    project_lines = [
        line
        for line in candidates
        if any(
            marker in line.lower()
            for marker in ("project", "проек", "developed", "built", "implemented", "launched")
        )
    ]
    return project_lines[:6]


def extract_responsibilities(text: str) -> List[str]:
    lines = split_lines(text)
    responsibility_markers = ("respons", "будет", "задач", "обязан", "you will", "we expect")
    matched = [line for line in lines if any(marker in line.lower() for marker in responsibility_markers)]
    return matched[:8]


def extract_domain_keywords(text: str) -> List[str]:
    keywords = []
    for phrase in (
        "microservices",
        "design system",
        "analytics",
        "payments",
        "admin panel",
        "ci/cd",
        "docker",
        "cloud",
        "a/b testing",
        "monitoring",
    ):
        if phrase in text.lower():
            keywords.append(phrase)
    return keywords


def extract_experience_years(text: str) -> int:
    patterns = [
        r"(\d+)\+?\s+years",
        r"(\d+)\+?\s+year",
        r"(\d+)\+?\s+лет",
        r"(\d+)\+?\s+года",
    ]
    values = []
    lowered = text.lower()
    for pattern in patterns:
        values.extend(int(match) for match in re.findall(pattern, lowered))
    return max(values) if values else 0


def detect_seniority_signals(text: str) -> List[str]:
    lowered = text.lower()
    signals = []
    for phrase in (
        "mentored",
        "led",
        "ownership",
        "cross-functional",
        "architecture",
        "technical decision",
        "team lead",
        "stakeholder",
    ):
        if phrase in lowered:
            signals.append(phrase)
    return signals[:6]


def infer_strengths(skills: List[str], projects: List[str]) -> List[str]:
    strengths = []
    if len(skills) >= 4:
        strengths.append("Широкий стек по целевой роли уже просматривается в резюме.")
    if projects:
        strengths.append("Есть проектные эпизоды, которые можно использовать для resume-based interview block.")
    if "Testing" in skills:
        strengths.append("Есть сигнал про инженерную зрелость через тестирование.")
    return strengths[:4]


def infer_candidate_risks(role: str, skills: List[str], projects: List[str]) -> List[str]:
    expected = set(ROLE_SKILLS.get(role, {}).keys())
    missing = [skill for skill in expected if skill not in skills]
    risks = []
    if missing:
        risks.append(f"В резюме слабо выражены темы: {', '.join(missing[:4])}.")
    if not projects:
        risks.append("Мало явных project-based историй для глубоких follow-up вопросов.")
    return risks[:4]


def summarize_text_density(text: str) -> Dict[str, object]:
    return {
        "char_count": len(text),
        "line_count": len(split_lines(text)),
        "has_content": bool(text.strip()),
    }


def infer_risk_level(missing_count: int, required_count: int) -> str:
    if required_count == 0:
        return "unknown"
    ratio = missing_count / max(required_count, 1)
    if ratio >= 0.5:
        return "high"
    if ratio >= 0.25:
        return "medium"
    return "low"


def map_skill_to_topic(role: str, skill: str) -> str:
    frontend_map = {
        "JavaScript": "JavaScript fundamentals",
        "TypeScript": "TypeScript typing and narrowing",
        "React": "React component model",
        "State Management": "State management and data flow",
        "HTML/CSS": "Browser rendering and layout fundamentals",
        "Testing": "Testing fundamentals",
        "API Integration": "API integration and async flows",
        "Performance": "Performance and optimization basics",
        "Browser Fundamentals": "Browser rendering and event loop",
    }
    java_map = {
        "Java": "Core Java and collections",
        "Spring": "Spring Boot basics",
        "SQL": "SQL and indexing basics",
        "REST APIs": "REST API design",
        "Concurrency": "Concurrency and multithreading basics",
        "Transactions": "Transactions and data consistency",
        "Caching": "Caching basics",
        "Messaging": "Messaging and async communication basics",
        "Testing": "Testing fundamentals",
    }
    mapper = frontend_map if role == "Frontend Developer" else java_map
    return mapper.get(skill, skill)


def build_topic_reason(topic: str, missing_skills: List[str], projects: List[str]) -> str:
    if any(token.lower() in topic.lower() for token in missing_skills):
        return "Тема попала в план, потому что навык явно требуется вакансией, но слабо подтверждён в резюме."
    if "Resume-based" in topic and projects:
        return "Тема нужна для проверки глубины реального опыта по проектам из резюме."
    return "Тема включена как базовый блок для целевой роли и уровня."


def split_lines(text: str) -> List[str]:
    return [line.strip(" -•\t") for line in text.splitlines() if line.strip()]
