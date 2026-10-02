from dataclasses import dataclass


@dataclass(frozen=True)
class CareerDefinition:
    name: str
    keywords: tuple[str, ...]
    parent: str | None = None


CAREER_TAXONOMY: dict[str, CareerDefinition] = {
    "software_engineering": CareerDefinition(
        "Software Engineering",
        (
            "software",
            "developer",
            "programming",
            "javascript",
            "typescript",
            "python",
            "rust",
            "java",
            "linux",
            "open source",
            "engineering",
            "technical",
        ),
    ),
    "frontend_engineering": CareerDefinition(
        "Frontend Engineering",
        ("frontend", "front-end", "javascript", "typescript", "react", "web developer"),
        "software_engineering",
    ),
    "backend_engineering": CareerDefinition(
        "Backend Engineering",
        ("backend", "back-end", "python", "django", "java", "api", "database"),
        "software_engineering",
    ),
    "cloud_engineering": CareerDefinition(
        "Cloud Engineering",
        ("cloud", "aws", "azure", "kubernetes", "devops", "infrastructure"),
        "software_engineering",
    ),
    "cybersecurity": CareerDefinition(
        "Cybersecurity",
        ("cybersecurity", "security", "infosec", "owasp", "hacking"),
        "software_engineering",
    ),
    "machine_learning": CareerDefinition(
        "Machine Learning",
        ("machine learning", "artificial intelligence", " ai ", "llm", "data science"),
        "software_engineering",
    ),
    "data_engineering": CareerDefinition(
        "Data Engineering",
        ("data engineering", "analytics", "sql", "database", "data platform"),
        "software_engineering",
    ),
    "product_management": CareerDefinition(
        "Product Management", ("product manager", "product management", "product strategy")
    ),
    "design": CareerDefinition("Design", ("design", "designer", "ux", "ui", "creative")),
    "marketing": CareerDefinition(
        "Marketing", ("marketing", "seo", "brand", "content strategy", "growth")
    ),
    "finance": CareerDefinition(
        "Finance", ("finance", "financial", "banking", "investment", "fintech")
    ),
    "accounting": CareerDefinition(
        "Accounting", ("accounting", "accountant", "cpa", "audit", "tax")
    ),
    "healthcare": CareerDefinition(
        "Healthcare", ("healthcare", "health care", "medical", "nursing", "clinical")
    ),
    "sales": CareerDefinition("Sales", ("sales", "business development", "revenue")),
    "operations": CareerDefinition(
        "Operations", ("operations", "supply chain", "logistics", "process")
    ),
}

ROLE_ALIASES: dict[str, str] = {
    "software engineer": "software_engineering",
    "software developer": "software_engineering",
    "web developer": "frontend_engineering",
    "frontend engineer": "frontend_engineering",
    "backend engineer": "backend_engineering",
    "devops engineer": "cloud_engineering",
    "site reliability engineer": "cloud_engineering",
    "security engineer": "cybersecurity",
    "data engineer": "data_engineering",
    "product manager": "product_management",
    "designer": "design",
    "marketer": "marketing",
    "accountant": "accounting",
}


def resolve_career(query: str) -> set[str]:
    normalized = " ".join(query.lower().replace("_", " ").split())
    direct = ROLE_ALIASES.get(normalized)
    if direct:
        return {direct}

    matched = {
        slug
        for slug, definition in CAREER_TAXONOMY.items()
        if normalized == definition.name.lower()
        or any(keyword.strip() in normalized for keyword in definition.keywords)
    }
    return matched or {normalized.replace(" ", "_")}


def related_careers(slugs: set[str]) -> set[str]:
    related = set(slugs)
    for slug, definition in CAREER_TAXONOMY.items():
        if definition.parent in slugs:
            related.add(slug)
        if slug in slugs and definition.parent:
            related.add(definition.parent)
    return related
