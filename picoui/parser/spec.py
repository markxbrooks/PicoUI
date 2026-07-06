from dataclasses import dataclass


@dataclass
class ArgParseSpec:
    """ArgParseSpec"""

    prog: str = ""
    description: str = ""
    usage: str = ""
    type = None


@dataclass
class ParserSpec:
    """Parser Spec"""

    obj: str = None
    long: str = None
    dest: str = None
    default: str = None
    choices: list = None
    help_text: str = None
    type: str = None