import re
from pathlib import Path
from typing import Annotated

import typer
from rich import print
from rich.progress import track

from responses import (
    ListWordsResponse,
    Node,
    get_question_message,
    system_message,
    registered_responses,
    response_tree,
)
from utils import Model, get_client, MessageQueue

app = typer.Typer(rich_help_panel='rich', no_args_is_help=True)


class Parser:
    def __init__(self, data_path: Path, output_path: Path, model: Model) -> None:
        self.data_path = data_path
        self.pattern = re.compile(r'\d+')
        print(f'[bold green]Working with {model}[/]')
        self.client = get_client(model, registered_responses)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.file = output_path.open('w', encoding='utf-8')
        self.pad = ' ' * 4

    def parse_word(
        self, queue: MessageQueue, word: str, node: Node, indent: int = 0
    ) -> None:
        self.file.write(f"\n{self.pad*indent}Word: {word}\n")
        queue.register_user_message(node.response_type.get_question(word))
        response = self.client.request(queue, node.response_type)
        try:
            res = node.response_type.model_validate_json(response)
        except Exception as e:
            print(response)
            print('[bold yellow]LLM has returned an invalid JSON![/]')
            raise e
        self.file.write(f'{self.pad*(indent+1)}{res}\n')
        for i, child in enumerate(node.children):
            word_part = res.get_part(word, i)
            if child and word_part:
                self.parse_word(queue, word_part, child, indent + 1)

    def parse_sentence(self, sentence: str) -> None:
        self.file.write(f"Sentence: {sentence}\n")
        queue = MessageQueue()
        queue.register_system_message(system_message)
        queue.register_user_message(get_question_message(sentence))
        response = self.client.request(queue, ListWordsResponse)
        try:
            words = ListWordsResponse.model_validate_json(response).words
        except Exception as e:
            print(response)
            print('[bold yellow]LLM has returned an invalid JSON![/]')
            words = []
        for word in words:
            try:
                self.parse_word(queue, word, response_tree)
            except Exception:
                print('[bold yellow]Sentence parsing failed![/]')
            self.file.write('\n')

    def parse(self) -> None:
        content = self.data_path.read_text(encoding='utf-8')

        sentences = [s.strip() for s in self.pattern.split(content) if s.strip()]
        for sentence in track(sentences, description='Sentence'):
            self.parse_sentence(sentence)

    def __enter__(self) -> 'Parser':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.file.close()


@app.command(no_args_is_help=True)
def parse(
    data_path: Annotated[
        Path,
        typer.Option(
            '--data',
            '-d',
            exists=True,
            file_okay=True,
            help='Path to the input file with sentences',
        ),
    ],
    output_path: Annotated[
        Path,
        typer.Option(
            '--output',
            '-o',
            help='Path to the output file',
        ),
    ],
    model_name: Annotated[
        str,
        typer.Option(
            '--model',
            '-m',
            help='Model name',
        ),
    ] = 'free',
) -> None:
    '''
    Parse Syriac sentences.
    '''
    model = Model[model_name.replace('-', '_').upper()]
    with Parser(data_path, output_path, model) as parser:
        parser.parse()


if __name__ == '__main__':
    app()
