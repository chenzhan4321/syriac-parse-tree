import re
from typing import Any, cast

from jsonref import replace_refs
from openai.types.chat import ChatCompletionToolParam
from pydantic import BaseModel

pattern = re.compile(r'(?<!^)(?=[A-Z])')


def get_name(model: type[BaseModel]) -> str:
    return pattern.sub('_', model.__name__).lower()


def purge_keys(d: dict[str, Any], k: list[str]) -> None:
    if isinstance(d, dict):
        for key in list(d.keys()):
            if key in k and 'type' in d.keys():
                del d[key]
            else:
                purge_keys(d[key], k)


def json_schema(model: type[BaseModel]) -> dict[str, Any]:
    schema = cast(
        dict[str, Any], replace_refs(model.model_json_schema(), proxies=False)
    )
    if '$defs' in schema:
        schema.pop('$defs')
    purge_keys(schema, ['title', 'default'])
    return schema


def pydantic_function_tool(model: type[BaseModel], name: str | None = None) -> ChatCompletionToolParam:
    schema = json_schema(model)

    return cast(
        ChatCompletionToolParam,
        {
            'type': 'function',
            'function': {
                'name': name or get_name(model),
                'strict': True,
                'description': schema.pop('description'),
                'parameters': schema,
            },
        },
    )
