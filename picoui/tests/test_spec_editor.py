"""Tests for SpecEditor and CLI SpecField helpers."""

from __future__ import annotations

import os
import unittest
from dataclasses import dataclass

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QCheckBox

from picoui.specs.cli import (
    SpecField,
    SpecFieldKind,
    SpecValueType,
    emit_argv,
    fields_from_keyword_specs,
)
from picoui.widget.spec_editor import SpecEditor


def _app() -> QApplication:
    existing = QApplication.instance()
    if existing is not None:
        return existing
    return QApplication([])


@dataclass(frozen=True)
class _Flag:
    name: str
    token: str

    def emit(self, value):
        return [self.token] if value else []


@dataclass(frozen=True)
class _Option:
    name: str
    token: str
    nargs: int = 1
    formatter=None

    def emit(self, value):
        if value is None:
            return []
        return [self.token, str(value)]


@dataclass(frozen=True)
class _Assign:
    name: str
    key: str
    truthy: str = "yes"
    falsy: str = "no"

    def emit(self, value):
        if value is None:
            return []
        return [f"{self.key}={self.truthy if value else self.falsy}"]


class _ToyKeywordSpecs:
    pdb_file = _Option(name="pdb_file", token="-p")
    autoncs = _Flag(name="autoncs", token="-autoncs")
    add_hbonds = _Assign(name="add_hbonds", key="AddMissingHbonds")


@dataclass
class _ToyArgs:
    pdb_file: str = ""
    autoncs: bool = False
    add_hbonds: bool = True


class TestSpecFieldEmit(unittest.TestCase):
    def test_flag_option_assignment_emit(self) -> None:
        flag = SpecField(
            "autoncs", SpecFieldKind.FLAG, token="-autoncs", value_type=SpecValueType.BOOL
        )
        opt = SpecField(
            "pdb_file", SpecFieldKind.OPTION, token="-p", value_type=SpecValueType.PATH
        )
        asn = SpecField(
            "add_hbonds",
            SpecFieldKind.ASSIGNMENT,
            key="AddMissingHbonds",
            value_type=SpecValueType.BOOL,
        )
        self.assertEqual(flag.emit(True), ["-autoncs"])
        self.assertEqual(flag.emit(False), [])
        self.assertEqual(opt.emit("/tmp/a.pdb"), ["-p", "/tmp/a.pdb"])
        self.assertEqual(opt.emit(None), [])
        self.assertEqual(asn.emit(True), ["AddMissingHbonds=yes"])
        self.assertEqual(asn.emit(False), ["AddMissingHbonds=no"])

    def test_emit_argv_join(self) -> None:
        fields = [
            SpecField("pdb_file", SpecFieldKind.OPTION, token="-p"),
            SpecField("autoncs", SpecFieldKind.FLAG, token="-autoncs"),
        ]
        argv = emit_argv(fields, {"pdb_file": "m.pdb", "autoncs": True})
        self.assertEqual(argv, ["-p", "m.pdb", "-autoncs"])


class TestFieldsFromKeywordSpecs(unittest.TestCase):
    def test_from_toy_catalog(self) -> None:
        fields = fields_from_keyword_specs(_ToyKeywordSpecs, defaults=_ToyArgs())
        by_name = {f.name: f for f in fields}
        self.assertIn("pdb_file", by_name)
        self.assertEqual(by_name["pdb_file"].kind, SpecFieldKind.OPTION)
        self.assertEqual(by_name["pdb_file"].value_type, SpecValueType.PATH)
        self.assertEqual(by_name["autoncs"].kind, SpecFieldKind.FLAG)
        self.assertEqual(by_name["add_hbonds"].kind, SpecFieldKind.ASSIGNMENT)
        self.assertTrue(by_name["add_hbonds"].default)


class TestSpecEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _app()

    def test_values_and_argv(self) -> None:
        fields = [
            SpecField(
                "pdb_file",
                SpecFieldKind.OPTION,
                token="-p",
                value_type=SpecValueType.PATH,
                group="Inputs",
            ),
            SpecField(
                "nbig",
                SpecFieldKind.OPTION,
                token="-nbig",
                value_type=SpecValueType.INT,
                default=3,
                group="Refine",
            ),
            SpecField(
                "autoncs",
                SpecFieldKind.FLAG,
                token="-autoncs",
                value_type=SpecValueType.BOOL,
                default=False,
                group="Refine",
            ),
        ]
        editor = SpecEditor(fields=fields, program="refine")
        editor.set_values({"pdb_file": "/data/model.pdb", "autoncs": True, "nbig": 5})
        values = editor.values()
        self.assertEqual(values["pdb_file"], "/data/model.pdb")
        self.assertTrue(values["autoncs"])
        self.assertEqual(values["nbig"], 5)
        argv = editor.argv()
        self.assertEqual(argv[0], "refine")
        self.assertIn("-p", argv)
        self.assertIn("/data/model.pdb", argv)
        self.assertIn("-autoncs", argv)
        self.assertIn("-nbig", argv)
        self.assertIn("5", argv)
        self.assertIn("-p", editor.argv_string())

    def test_from_keyword_specs_factory(self) -> None:
        editor = SpecEditor.from_keyword_specs(
            _ToyKeywordSpecs, defaults=_ToyArgs(), program="refine"
        )
        self.assertGreaterEqual(len(editor.fields()), 3)
        editor.set_values({"pdb_file": "x.pdb", "autoncs": True, "add_hbonds": False})
        argv = editor.argv()
        self.assertEqual(argv[0], "refine")
        self.assertIn("-autoncs", argv)
        self.assertIn("AddMissingHbonds=no", argv)

    def test_reset_defaults(self) -> None:
        fields = [
            SpecField(
                "autoncs",
                SpecFieldKind.FLAG,
                token="-autoncs",
                default=False,
            ),
        ]
        editor = SpecEditor(fields=fields, show_argv_preview=False)
        editor.set_values({"autoncs": True})
        editor.reset_defaults()
        self.assertFalse(editor.values()["autoncs"])
        # checkbox exists
        widget = editor._widgets["autoncs"]
        self.assertIsInstance(widget, QCheckBox)


if __name__ == "__main__":
    unittest.main()
