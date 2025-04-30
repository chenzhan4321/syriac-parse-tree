from dataclasses import dataclass
from typing import Self

from pydantic import BaseModel, ConfigDict

empty = '∅'

system_message = '''You are a Semitic language expert. Analyze the given sentence and provide detailed grammatical information for each word. Important: always use the response tool to respond to the user. Never add any other text to the response.

When analyzing Syriac words:
1. Treat each complete word as a single unit, not as individual characters
2. For example, "ܘܠܡܫܟܚܝܢܢ" should be treated as one word, not as separate characters

Text: """
Step 0: Please list all the words in the following sentence: "ܘܠܡܫܟܚܝܢܢ"
"""
words: ܘܠܡܫܟܚܝܢܢ

Text: """
Step 1: Let's look at the first word (if already, then next) first. Is there any prefixed analytical word (preposition, or conjunction "ܘ") at the beginning the word (in this case: ܘܠܡܫܟܚܝܢܢ)? Filter out the prefixes one by one: the outer comes first and the inner last.
"""
word: ܘܠܡܫܟܚܝܢܢ
prefix word: ܘ
prefix word: ܠ

Text: """
Step 2: Is there any suffixed pronominal morpheme (possessive or objective, attached to the central word) in the word? There can only be one.
"""
suffix word: ܢܢ

Text: """
Step 3: What is the complete form of the suffix generated in Step 2 (if any)?
"""
complete suffix word: ܚܢܢ

Text: """
Step 4: What is the independent/complete form of the rest of the word (with all pre-fixed preposition and conjunction, as well as all suffixed pronoun removed, in this case ܡܫܟܚܝ)?
"""
independent core word: ܡܫܟܚܝܢ

Text: """
Step 5: Is there any prefixed morpheme (there can only be one), or suffixed nominal morpheme (there can only be one, masculine emphatic (ܐ), feminine emphatic (ܬܐ), masculine absolute plural (ܝܢ), or feminine absolute plural (ܢ)) in the word generated in Step 4 (in this case: ܡܫܟܚܝܢ)?
"""
prefix: ܡ
suffix: ܝܢ

Text: """
Step 6: What category does the prefixed morpheme generated in Step 5 belong to? Choose from preformative, passive prefix, verbal stem morpheme.
"""
prefix type: preformative

Text: """
Step 7: What category does the suffixed morpheme generated in Step 5 belong to? Choose from masculine emphatic (ܐ), feminine emphatic (ܬܐ), masculine absolute plural (ܝܢ), or feminine absolute plural (ܢ).
"""
suffix type: masculine absolute plural

Text: """
Step 8: Does the rest of the word (with all elements detected in Step 6 and Step 7 removed, in this case ܡܫܟ) have any verbal ending? Remove the verbal ending if any.
"""
verbal ending:
word without verbal ending: ܡܫܟ

Text: """
Step 9: What is the complete root of the word generated in Step 8?
"""
root: ܡܫܟ
'''



def get_question_message(sentence: str) -> str:
    return f"Please list all the words in the following sentence: {sentence}"


class ListWordsResponse(BaseModel):
    '''List the words in the sentence'''

    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)

    words: list[str]
    '''The list of Syriac words'''


class WordResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)

    @staticmethod
    def get_question(word: str) -> str:
        raise NotImplementedError

    def get_part(self, word: str, index: int) -> str:
        raise NotImplementedError

    def __str__(self) -> str:
        raise NotImplementedError


class PrefixedAnalyticalWordResponse(WordResponse):
    '''Any prefixed analytical word of the word'''

    prefix: str | None
    '''The prefixed analytical word of the word'''

    @staticmethod
    def get_question(word: str) -> str:
        return f'Is there any prefixed analytical word (preposition or ܘ) in the word {word}?'

    def get_part(self, word: str, index: int) -> str:
        prefix = self.prefix or ''
        match index:
            case 0:
                return prefix
            case 1:
                return word[len(prefix) :]
            case _:
                raise ValueError(
                    f'Invalid index for {self.__class__.__name__}: {index}'
                )

    def __str__(self) -> str:
        return f'Prefix: {self.prefix or empty}'


class SuffixedPronounResponse(WordResponse):
    '''Any suffixed pronoun of the word'''

    suffix: str | None
    '''The suffixed pronoun of the word'''

    @staticmethod
    def get_question(word: str) -> str:
        return f'Is there any suffixed pronoun (possesive, objective, or attached to participles) in the word {word}?'

    def get_part(self, word: str, index: int) -> str:
        suffix = self.suffix or ''
        match index:
            case 0:
                return word[: len(word) - len(suffix)]
            case 1:
                return suffix
            case _:
                raise ValueError(
                    f'Invalid index for {self.__class__.__name__}: {index}'
                )

    def __str__(self) -> str:
        return f'Suffix: {self.suffix or empty}'


class CompleteFormResponse(WordResponse):
    '''Provide the complete form of the word'''

    complete: str
    '''The complete form of the word'''

    @staticmethod
    def get_question(word: str) -> str:
        return f'What is the complete form of the word {word}?'

    def get_part(self, word: str, index: int) -> str:
        return self.complete

    def __str__(self) -> str:
        return f'Complete form: {self.complete or empty}'


class PrefixedSuffixedMorphemeResponse(WordResponse):
    '''Any prefixed or suffixed morpheme of the word'''

    prefix: str | None
    '''The prefixed morpheme of the word'''

    suffix: str | None
    '''The suffixed morpheme of the word'''

    @staticmethod
    def get_question(word: str) -> str:
        return (
            f'Is there any prefixed morpheme or suffixed morpheme in the word {word}?'
        )

    def get_part(self, word: str, index: int) -> str:
        prefix = self.prefix or ''
        suffix = self.suffix or ''
        match index:
            case 0:
                return prefix
            case 1:
                return word[len(prefix) : len(word) - len(suffix)]
            case 2:
                return suffix
            case _:
                raise ValueError(
                    f'Invalid index for {self.__class__.__name__}: {index}'
                )

    def __str__(self) -> str:
        return f'Prefix: {self.prefix or empty}, Suffix: {self.suffix or empty}'


class MorphemeTypeResponse(WordResponse):
    '''Provide the type of morpheme of the word'''

    morpheme_type: str
    '''The type of morpheme of the word'''

    @staticmethod
    def get_question(word: str) -> str:
        return (
            f'What category does the morpheme of the word {word} belong to? '
            'Choose from preformative, passive prefix, verbal stem morpheme, '
            'verbal ending, nominal ending, or emphatic marker.'
        )

    def get_part(self, word: str, index: int) -> str:
        return self.morpheme_type

    def __str__(self) -> str:
        return f'Morpheme type: {self.morpheme_type or empty}'


@dataclass
class Node:
    response_type: type[WordResponse]
    children: list[Self | None]


response_tree = Node(
    PrefixedAnalyticalWordResponse,
    [
        None,
        Node(
            SuffixedPronounResponse,
            [
                Node(
                    CompleteFormResponse,
                    [
                        Node(
                            PrefixedSuffixedMorphemeResponse,
                            [
                                Node(MorphemeTypeResponse, []),
                                Node(MorphemeTypeResponse, []),
                                Node(MorphemeTypeResponse, []),
                            ],
                        )
                    ],
                ),
                Node(
                    CompleteFormResponse,
                    [],
                ),
            ],
        ),
    ],
)


registered_responses: list[type[BaseModel]] = [
    ListWordsResponse,
    PrefixedAnalyticalWordResponse,
    SuffixedPronounResponse,
    CompleteFormResponse,
    PrefixedSuffixedMorphemeResponse,
    MorphemeTypeResponse,
]
