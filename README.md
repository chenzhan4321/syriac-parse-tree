# syriac-parse-tree
A Syriac language parser based on tree structures.

Prerequisites:
- typer
- openai
- dashscope
- jsonref

## Sanity Test

```console
python parser.py -d data/test.txt -o output/test.txt -m plus
```

This will produce the same parse tree as the one-shot example encoded in the system message.

> [!CAUTION]
> We recommend using models stronger than `qwen-turbo`, as weaker models may not produce valid JSON format strings.

> [!NOTE]
> More models will be supported, *stay tuned!*

## Isaiah Test

```console
python parser.py -d data/isaiah_test.txt -o output/isaiah_test.txt -m plus
```

This will produce the parse trees for the first 2 sentences in Isaiah.