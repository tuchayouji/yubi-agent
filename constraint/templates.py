from .rules import GENERATE_RULES, REWRITE_RULES, GENRE_TEMPLATES


def get_constraint_template(mode: str, genre: str = None) -> str:
    if mode == "generate":
        template = GENERATE_RULES
    elif mode == "rewrite":
        template = REWRITE_RULES
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'generate' or 'rewrite'.")

    if genre and genre in GENRE_TEMPLATES:
        template += "\n" + GENRE_TEMPLATES[genre]

    return template
