from .rules import GENERATE_RULES, REWRITE_RULES


def get_constraint_template(mode: str) -> str:
    if mode == "generate":
        return GENERATE_RULES
    elif mode == "rewrite":
        return REWRITE_RULES
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'generate' or 'rewrite'.")
