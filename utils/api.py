import os
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from enum import StrEnum, auto
from http import HTTPStatus
from typing import Any, cast

import dashscope
from dashscope.api_entities.dashscope_response import GenerationResponse
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel
from rich import print

from config import DASHSCOPE_API_KEY
from .schema import pydantic_function_tool


class Role(StrEnum):
    SYSTEM = auto()
    USER = auto()
    ASSISTANT = auto()
    TOOL = auto()


class Model(StrEnum):
    FREE = 'qwen2.5-1.5b-instruct'
    TURBO = 'qwen-turbo'
    PLUS = 'qwen-plus'
    MAX = 'qwen-max'
    MAX_0919 = 'qwen-max-0919'
    LLAMA = 'llama3.1-405b-instruct'


@dataclass
class Message:
    role: str
    content: str
    tool_calls: list[Any] | None = None

    def cast(self) -> ChatCompletionMessageParam:
        param = asdict(self)
        if param['tool_calls'] is None:
            del param['tool_calls']
        return cast(ChatCompletionMessageParam, param)


@dataclass
class ToolMessage(Message):
    tool_call_id: str = ''
    name: str = ''


class MessageQueue:
    def __init__(self) -> None:
        self.messages: list[Message] = []
        self.argument: str = ''

    def get_messages(self) -> list[ChatCompletionMessageParam]:
        return [message.cast() for message in self.messages]

    def register_message(self, role: str, content: str) -> None:
        self.messages.append(Message(role, content))

    def register_system_message(self, content: str) -> None:
        self.register_message(Role.SYSTEM, content)
    
    def register_user_message(self, content: str) -> None:
        self.register_message(Role.USER, f'Text: """\n{content}\n"""')

    def register_response(self, completion: GenerationResponse) -> None:
        if completion.status_code == HTTPStatus.OK:
            message = completion.output.choices[0].message
            calls = message.tool_calls
            self.messages.append(Message(Role.ASSISTANT, message.content, calls))
            self.messages.append(
                ToolMessage(
                    Role.TOOL, '', None, calls[0]['id'], calls[0]['function']['name']
                )
            )
            self.argument = calls[0]['function']['arguments']
        else:
            print(
                f'[bold yellow]Request error {completion.code}: {completion.message}[/]'
            )
            self.argument = ''


class Client(ABC):
    def __init__(
        self,
        model: Model,
        tools: list[type[BaseModel]],
        temperature: int = 0,
        seed: int = 42,
    ) -> None:
        self.model = model
        self.tools = {tool.__name__: pydantic_function_tool(tool) for tool in tools}
        self.temperature = temperature
        self.seed = seed

    @abstractmethod
    def request(self, queue: MessageQueue, tool: type[BaseModel]) -> str: ...


class ClientDashScope(Client):
    def __init__(
        self,
        model: Model,
        tools: list[type[BaseModel]],
        temperature: int = 0,
        seed: int = 42,
    ) -> None:
        super().__init__(model, tools, temperature, seed)

    def request(self, queue: MessageQueue, tool: type[BaseModel]) -> str:
        completion = dashscope.Generation.call(
            api_key=DASHSCOPE_API_KEY,
            model=self.model,
            messages=queue.get_messages(),
            result_format='message',
            tools=[self.tools[tool.__name__]],
            tool_choice={
                'type': 'function',
                'function': {
                    'name': self.tools[tool.__name__]['function']['name'],
                },
            },
            temperature=self.temperature,
            seed=self.seed,
        )
        assert isinstance(completion, GenerationResponse)
        queue.register_response(completion)
        return queue.argument


def get_client(
    model: Model,
    tools: list[type[BaseModel]],
    temperature: int = 0,
    seed: int = 42,
) -> Client:
    match model:
        case _:
            return ClientDashScope(model, tools, temperature, seed)
