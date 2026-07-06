"""
This module provides functionality to create and configure ArgumentParser
instances based on provided specifications.

The module focuses on integrating custom specifications into argparse parsers.
It includes tools for adding arguments to a parser from a specification and
constructing parsers from specification objects.
"""

import argparse
from argparse import ArgumentParser

from picoui.parser.spec import ArgParseSpec, ParserSpec


def add_arg_to_parser_from_spec(parser: ArgumentParser, parser_file_spec: ParserSpec):
    """add arg to parser from spec"""
    parser.add_argument(
        parser_file_spec.obj,
        parser_file_spec.long,
        dest=parser_file_spec.dest,
        help=parser_file_spec.help_text,
    )


def parser_from_arg_parse_spec(arg_parse_spec: ArgParseSpec) -> ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=arg_parse_spec.prog,
        description=arg_parse_spec.description,
        usage=arg_parse_spec.usage,
    )
    return parser