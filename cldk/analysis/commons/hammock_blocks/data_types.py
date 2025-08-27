from enum import Enum


class ParsingMode(str, Enum):
    simple = "simple"
    rule_based = "rule_based"
