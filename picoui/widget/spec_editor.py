"""Generic Qt editor for CLI program flags / options (MxLib KeywordSpecs).

Typical usage::

    from picoui.specs.cli import SpecField, SpecFieldKind, SpecValueType
    from picoui.widget.spec_editor import SpecEditor

    editor = SpecEditor(fields=[
        SpecField("pdb_file", SpecFieldKind.OPTION, token="-p",
                  value_type=SpecValueType.PATH, group="Inputs"),
        SpecField("autoncs", SpecFieldKind.FLAG, token="-autoncs",
                  value_type=SpecValueType.BOOL, default=False),
    ])
    editor.set_values({"pdb_file": "/data/model.pdb"})
    print(editor.argv())  # ['-p', '/data/model.pdb']

Or from an MxLib catalog::

    from mxlib.domain.gphl.wrappers.buster.keyword_specs import BusterKeywordSpecs
    from picoui.specs.cli import fields_from_keyword_specs
    editor = SpecEditor(fields=fields_from_keyword_specs(BusterKeywordSpecs))
"""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from picoui.specs.cli import (
    SpecField,
    SpecFieldKind,
    SpecValueType,
    emit_argv,
    fields_from_keyword_specs,
)


class SpecEditor(QWidget):
    """Scrollable form that edits CLI keyword values and previews argv.

    Emits :attr:`valuesChanged` whenever any field changes.
    """

    valuesChanged = Signal(dict)

    def __init__(
        self,
        fields: list[SpecField] | None = None,
        parent: QWidget | None = None,
        *,
        show_argv_preview: bool = True,
        program: str = "",
    ) -> None:
        super().__init__(parent)
        self._fields: list[SpecField] = []
        self._widgets: dict[str, QWidget] = {}
        self._program = program
        self._show_argv_preview = show_argv_preview
        self._updating = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._form_host = QWidget()
        self._form_layout = QVBoxLayout(self._form_host)
        self._form_layout.setContentsMargins(4, 4, 4, 4)
        self._form_layout.addStretch(1)
        self._scroll.setWidget(self._form_host)
        root.addWidget(self._scroll, stretch=1)

        if show_argv_preview:
            preview_box = QGroupBox("Command preview")
            preview_layout = QVBoxLayout(preview_box)
            self._argv_view = QTextEdit()
            self._argv_view.setReadOnly(True)
            self._argv_view.setMaximumHeight(72)
            mono = QFont("Menlo")
            if not mono.exactMatch():
                mono = QFont("Courier New")
            mono.setPointSize(11)
            self._argv_view.setFont(mono)
            preview_layout.addWidget(self._argv_view)
            root.addWidget(preview_box)
        else:
            self._argv_view = None

        if fields:
            self.set_fields(fields)

    # ------------------------------------------------------------------ API

    @classmethod
    def from_keyword_specs(
        cls,
        catalog: Any,
        parent: QWidget | None = None,
        *,
        defaults: Any | None = None,
        program: str = "",
        group: str = "Options",
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        show_argv_preview: bool = True,
    ) -> SpecEditor:
        """Build an editor from an MxLib ``*KeywordSpecs`` catalog."""
        fields = fields_from_keyword_specs(
            catalog,
            defaults=defaults,
            group=group,
            include=include,
            exclude=exclude,
        )
        return cls(
            fields=fields,
            parent=parent,
            show_argv_preview=show_argv_preview,
            program=program,
        )

    def set_program(self, program: str) -> None:
        """Prefix shown in the argv preview (e.g. ``refine``)."""
        self._program = program
        self._refresh_argv_preview()

    def set_fields(self, fields: list[SpecField]) -> None:
        """Replace all fields and rebuild the form."""
        self._fields = list(fields)
        self._rebuild_form()
        self._refresh_argv_preview()

    def fields(self) -> list[SpecField]:
        """Return the current field list."""
        return list(self._fields)

    def set_values(self, values: dict[str, Any]) -> None:
        """Populate widgets from a name → value mapping."""
        self._updating = True
        try:
            for name, value in values.items():
                widget = self._widgets.get(name)
                if widget is None:
                    continue
                self._write_widget(widget, value)
        finally:
            self._updating = False
        self._refresh_argv_preview()
        self.valuesChanged.emit(self.values())

    def values(self) -> dict[str, Any]:
        """Return current widget values keyed by field name."""
        out: dict[str, Any] = {}
        for field in self._fields:
            widget = self._widgets.get(field.name)
            if widget is None:
                continue
            out[field.name] = self._read_widget(widget, field)
        return out

    def argv(self) -> list[str]:
        """Return emitted CLI tokens for the current values."""
        tokens = emit_argv(self._fields, self.values())
        if self._program:
            return [self._program, *tokens]
        return tokens

    def argv_string(self) -> str:
        """Shell-quoted argv preview string."""
        return shlex.join(self.argv())

    def reset_defaults(self) -> None:
        """Restore each field to its declared default."""
        defaults = {
            f.name: f.default
            for f in self._fields
            if f.default is not None or f.kind is SpecFieldKind.FLAG
        }
        # Flags without default → False
        for f in self._fields:
            if f.kind is SpecFieldKind.FLAG and f.name not in defaults:
                defaults[f.name] = False
            if f.kind is SpecFieldKind.ASSIGNMENT and f.name not in defaults:
                defaults[f.name] = False
        self.set_values(defaults)

    # ------------------------------------------------------------------ form

    def _clear_form(self) -> None:
        while self._form_layout.count():
            item = self._form_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._widgets.clear()

    def _rebuild_form(self) -> None:
        self._clear_form()
        groups: dict[str, list[SpecField]] = {}
        for field in self._fields:
            groups.setdefault(field.group or "Options", []).append(field)

        for group_title, group_fields in groups.items():
            box = QGroupBox(group_title)
            form = QFormLayout(box)
            for field in group_fields:
                widget = self._make_widget(field)
                self._widgets[field.name] = widget
                if isinstance(widget, QCheckBox):
                    form.addRow(widget)
                else:
                    label = QLabel(field.display_label())
                    if field.help:
                        label.setToolTip(field.help)
                        widget.setToolTip(field.help)
                    form.addRow(label, widget)
                if field.default is not None or field.kind in (
                    SpecFieldKind.FLAG,
                    SpecFieldKind.ASSIGNMENT,
                ):
                    default = field.default
                    if default is None and field.kind in (
                        SpecFieldKind.FLAG,
                        SpecFieldKind.ASSIGNMENT,
                    ):
                        default = False
                    self._write_widget(widget, default)
            self._form_layout.insertWidget(self._form_layout.count() - 1, box)

        if self._form_layout.count() == 1:
            # only stretch
            empty = QLabel("No fields to edit.")
            self._form_layout.insertWidget(0, empty)

    def _make_widget(self, field: SpecField) -> QWidget:
        if field.value_type is SpecValueType.BOOL or field.kind in (
            SpecFieldKind.FLAG,
            SpecFieldKind.ASSIGNMENT,
        ):
            box = QCheckBox(field.display_label())
            if field.help:
                box.setToolTip(field.help)
            if field.kind is SpecFieldKind.FLAG and field.token:
                box.setText(f"{field.display_label()}  ({field.token})")
            elif field.kind is SpecFieldKind.ASSIGNMENT and field.key:
                box.setText(f"{field.display_label()}  ({field.key}=…)")
            box.toggled.connect(self._on_any_changed)
            return box

        if field.value_type is SpecValueType.INT:
            spin = QSpinBox()
            spin.setRange(-1_000_000_000, 1_000_000_000)
            spin.setSpecialValueText("")
            spin.valueChanged.connect(self._on_any_changed)
            return spin

        if field.value_type is SpecValueType.FLOAT:
            spin = QDoubleSpinBox()
            spin.setDecimals(4)
            spin.setRange(-1e9, 1e9)
            spin.valueChanged.connect(self._on_any_changed)
            return spin

        if field.choices:
            combo = QComboBox()
            combo.setEditable(True)
            combo.addItems(list(field.choices))
            combo.currentTextChanged.connect(self._on_any_changed)
            return combo

        if field.value_type in (SpecValueType.PATH, SpecValueType.DIR):
            return self._make_path_row(field)

        edit = QLineEdit()
        if field.token:
            edit.setPlaceholderText(field.token)
        edit.textChanged.connect(self._on_any_changed)
        return edit

    def _make_path_row(self, field: SpecField) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        edit = QLineEdit()
        edit.setObjectName("path_edit")
        if field.token:
            edit.setPlaceholderText(field.token)
        edit.textChanged.connect(self._on_any_changed)
        layout.addWidget(edit, stretch=1)
        browse = QPushButton("Browse…")
        directory = field.value_type is SpecValueType.DIR

        def _browse() -> None:
            start = edit.text().strip() or str(Path.home())
            if directory:
                path = QFileDialog.getExistingDirectory(
                    self, f"Select {field.display_label()}", start
                )
            else:
                path, _ = QFileDialog.getOpenFileName(
                    self, f"Select {field.display_label()}", start
                )
            if path:
                edit.setText(path)

        browse.clicked.connect(_browse)
        layout.addWidget(browse)
        return row

    def _on_any_changed(self, *_args: Any) -> None:
        if self._updating:
            return
        self._refresh_argv_preview()
        self.valuesChanged.emit(self.values())

    def _refresh_argv_preview(self) -> None:
        if self._argv_view is None:
            return
        self._argv_view.setPlainText(self.argv_string())

    # ------------------------------------------------------------------ I/O

    def _read_widget(self, widget: QWidget, field: SpecField) -> Any:
        if isinstance(widget, QCheckBox):
            return bool(widget.isChecked())
        if isinstance(widget, QSpinBox) and not isinstance(widget, QDoubleSpinBox):
            return int(widget.value())
        if isinstance(widget, QDoubleSpinBox):
            return float(widget.value())
        if isinstance(widget, QComboBox):
            text = widget.currentText().strip()
            return text or None
        if isinstance(widget, QLineEdit):
            text = widget.text().strip()
            return text or None
        # path row
        edit = widget.findChild(QLineEdit, "path_edit")
        if edit is not None:
            text = edit.text().strip()
            return text or None
        return None

    def _write_widget(self, widget: QWidget, value: Any) -> None:
        if isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
            return
        if isinstance(widget, QSpinBox) and not isinstance(widget, QDoubleSpinBox):
            if value is None or value == "":
                return
            widget.setValue(int(value))
            return
        if isinstance(widget, QDoubleSpinBox):
            if value is None or value == "":
                return
            widget.setValue(float(value))
            return
        if isinstance(widget, QComboBox):
            text = "" if value is None else str(value)
            idx = widget.findText(text)
            if idx >= 0:
                widget.setCurrentIndex(idx)
            else:
                widget.setEditText(text)
            return
        if isinstance(widget, QLineEdit):
            widget.setText("" if value is None else str(value))
            return
        edit = widget.findChild(QLineEdit, "path_edit")
        if edit is not None:
            edit.setText("" if value is None else str(value))
