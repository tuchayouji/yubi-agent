from .templates import get_constraint_template


def apply_constraint(messages: list, mode: str, genre: str = None) -> list:
    constraint_template = get_constraint_template(mode, genre)

    result = []
    for msg in messages:
        if msg["role"] == "system":
            new_content = msg["content"] + "\n\n" + constraint_template
            result.append({"role": "system", "content": new_content})
        else:
            result.append(msg)

    if not any(m["role"] == "system" for m in result):
        result.insert(0, {"role": "system", "content": constraint_template})

    return result
