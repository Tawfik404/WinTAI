import logging

from services.executor.registry import get_tool

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    ...


_SCHEMA_TYPES = {
    "str": str,
    "bool": bool,
    "int": int,
    "float": float,
}


def validate(tool_name: str, params: dict) -> dict:
    tool_def = get_tool(tool_name)
    if tool_def is None:
        raise ValidationError(f"Unknown tool: {tool_name}")

    schema = tool_def.get("params_schema", {})
    validated: dict = {}

    for key, rules in schema.items():
        if rules.get("required", False):
            if key not in params or params[key] is None:
                raise ValidationError(f"Missing required parameter: '{key}'")
            raw = params[key]
        elif key in params and params[key] is not None:
            raw = params[key]
        else:
            default = rules.get("default")
            if default is not None:
                validated[key] = default
            continue

        expected_type = _SCHEMA_TYPES.get(rules.get("type", "str"))
        if expected_type is not None and not isinstance(raw, expected_type):
            raise ValidationError(
                f"Parameter '{key}' expected {rules['type']}, got {type(raw).__name__}"
            )

        sanitized = _sanitize(raw)
        validated[key] = sanitized

    unknown = set(params.keys()) - set(schema.keys())
    if unknown:
        raise ValidationError(f"Unknown parameter(s): {', '.join(sorted(unknown))}")

    return validated


def _sanitize(value) -> str | bool | int | float:
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned != value:
            logger.debug("Trimmed whitespace from parameter")
        return cleaned
    return value
