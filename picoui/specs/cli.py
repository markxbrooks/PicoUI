"""Declarative field specs for editing CLI program flags / options.

These mirror MxLib's :mod:`mxlib.spec.keyword` shapes (``FlagSpec``,
``OptionSpec``, ``AssignmentSpec``) without depending on MxLib, so PicoUI
apps and DiffractionLab can share one editor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable, Sequence


class SpecFieldKind(str, Enum):
    """How a field is emitted on the command line."""

    FLAG = "flag"
    OPTION = "option"
    ASSIGNMENT = "assignment"


class SpecValueType(str, Enum):
    """Widget / coercion type for a field value."""

    BOOL = "bool"
    STR = "str"
    INT = "int"
    FLOAT = "float"
    PATH = "path"
    DIR = "dir"


@dataclass(frozen=True)
class SpecField:
    """One editable CLI argument.

    :param name: Stable key used in :meth:`SpecEditor.values` / ``set_values``.
    :param kind: Flag / option / ``key=yes|no`` assignment.
    :param label: Form label (defaults to a prettified ``name``).
    :param help: Tooltip / what’s-this text.
    :param token: CLI token for flags and options (e.g. ``-p``, ``-autoncs``).
    :param key: Assignment key for ``key=yes`` style tokens.
    :param value_type: Widget and parse type.
    :param default: Initial value (``None`` means unset / omit from argv).
    :param choices: Optional combo-box choices for string options.
    :param group: Group box / section title.
    :param nargs: Number of values after an option token.
    :param formatter: Optional emit-time value → ``list[str]`` (paths, etc.).
    :param truthy: Assignment true token (default ``yes``).
    :param falsy: Assignment false token (default ``no``).
    """

    name: str
    kind: SpecFieldKind
    label: str = ""
    help: str = ""
    token: str = ""
    key: str = ""
    value_type: SpecValueType = SpecValueType.STR
    default: Any = None
    choices: tuple[str, ...] = ()
    group: str = "Options"
    nargs: int = 1
    formatter: Callable[[Any], list[str]] | None = None
    truthy: str = "yes"
    falsy: str = "no"

    def display_label(self) -> str:
        """Human label for the form row."""
        if self.label:
            return self.label
        return self.name.replace("_", " ").strip().capitalize()

    def emit(self, value: Any) -> list[str]:
        """Convert *value* to argv tokens (same contract as MxLib KeywordSpec)."""
        if self.kind is SpecFieldKind.FLAG:
            return [self.token] if value else []

        if self.kind is SpecFieldKind.ASSIGNMENT:
            if value is None:
                return []
            return [f"{self.key}={self.truthy if value else self.falsy}"]

        # OPTION
        if value is None or value is False or value == "":
            return []
        if self.formatter is not None:
            values = self.formatter(value)
            # Empty formatter result means "omit this option" (e.g. auto / unset).
            if not values:
                return []
        elif isinstance(value, (list, tuple)):
            values = [str(v) for v in value]
        else:
            values = [str(value)]
        if len(values) != self.nargs:
            raise ValueError(
                f"{self.token or self.name} expects {self.nargs} values, "
                f"got {len(values)}"
            )
        return [self.token, *values] if self.token else list(values)


def iter_keyword_specs(catalog: Any) -> list[Any]:
    """Yield KeywordSpec-like attributes from a MxLib ``*KeywordSpecs`` class."""
    specs: list[Any] = []
    for attr in dir(catalog):
        if attr.startswith("_"):
            continue
        item = getattr(catalog, attr)
        if getattr(item, "name", None) and hasattr(item, "emit"):
            specs.append(item)
    return specs


def _infer_value_type(spec: Any, default: Any) -> SpecValueType:
    name = str(getattr(spec, "name", "") or "").lower()
    token = str(getattr(spec, "token", "") or "").lower()
    formatter = getattr(spec, "formatter", None)
    formatter_name = getattr(formatter, "__name__", "") if formatter else ""

    if default is True or default is False:
        return SpecValueType.BOOL
    if isinstance(default, int) and not isinstance(default, bool):
        return SpecValueType.INT
    if isinstance(default, float):
        return SpecValueType.FLOAT

    pathish = (
        "path" in formatter_name.lower()
        or name.endswith("_file")
        or name.endswith("_path")
        or name.endswith("_pdb")
        or "pdb" in name
        or "mtz" in name
        or name.endswith("_dat")
        or "ligand" in name
    )
    dirish = name.endswith("_dir") or name.endswith("_directory") or "output_dir" in name
    if dirish:
        return SpecValueType.DIR
    if pathish:
        return SpecValueType.PATH

    # Heuristic from token alone
    if any(k in token for k in ("-p", "-m", "-l", "-gelly", "-target")):
        return SpecValueType.PATH
    return SpecValueType.STR


def _infer_kind(spec: Any) -> SpecFieldKind:
    cls_name = type(spec).__name__
    if "Assignment" in cls_name or (hasattr(spec, "key") and not hasattr(spec, "token")):
        return SpecFieldKind.ASSIGNMENT
    if "Flag" in cls_name:
        return SpecFieldKind.FLAG
    if "Option" in cls_name:
        return SpecFieldKind.OPTION
    # Duck-type fallbacks
    if hasattr(spec, "key"):
        return SpecFieldKind.ASSIGNMENT
    if hasattr(spec, "nargs") or hasattr(spec, "formatter"):
        return SpecFieldKind.OPTION
    if hasattr(spec, "token"):
        return SpecFieldKind.FLAG
    raise TypeError(f"Unrecognized keyword spec: {spec!r}")


def fields_from_keyword_specs(
    catalog: Any,
    *,
    defaults: Any | None = None,
    group: str = "Options",
    include: Sequence[str] | None = None,
    exclude: Sequence[str] | None = None,
) -> list[SpecField]:
    """Build :class:`SpecField` rows from an MxLib ``*KeywordSpecs`` catalog.

    :param catalog: Class or instance with KeywordSpec attributes.
    :param defaults: Optional args dataclass / mapping for defaults and types.
    :param group: Default group title for all fields.
    :param include: If set, only these ``name`` keys.
    :param exclude: Names to skip.
    """
    include_set = set(include) if include is not None else None
    exclude_set = set(exclude or ())
    default_map: dict[str, Any] = {}
    if defaults is not None:
        if hasattr(defaults, "__dataclass_fields__"):
            default_map = {
                k: getattr(defaults, k)
                for k in defaults.__dataclass_fields__  # type: ignore[attr-defined]
            }
        elif isinstance(defaults, dict):
            default_map = dict(defaults)

    fields: list[SpecField] = []
    for raw in iter_keyword_specs(catalog):
        name = str(raw.name)
        if include_set is not None and name not in include_set:
            continue
        if name in exclude_set:
            continue
        kind = _infer_kind(raw)
        default = default_map.get(name, None)
        if kind is SpecFieldKind.FLAG:
            value_type = SpecValueType.BOOL
            if default is None:
                default = False
        elif kind is SpecFieldKind.ASSIGNMENT:
            value_type = SpecValueType.BOOL
            if default is None:
                default = False
        else:
            value_type = _infer_value_type(raw, default)

        fields.append(
            SpecField(
                name=name,
                kind=kind,
                token=str(getattr(raw, "token", "") or ""),
                key=str(getattr(raw, "key", "") or ""),
                value_type=value_type,
                default=default,
                group=group,
                nargs=int(getattr(raw, "nargs", 1) or 1),
                formatter=getattr(raw, "formatter", None),
                truthy=str(getattr(raw, "truthy", "yes")),
                falsy=str(getattr(raw, "falsy", "no")),
                help=str(getattr(raw, "token", "") or getattr(raw, "key", "") or ""),
            )
        )
    return fields


def emit_argv(fields: Iterable[SpecField], values: dict[str, Any]) -> list[str]:
    """Join emitted tokens for all *fields* using *values*."""
    argv: list[str] = []
    by_name = {f.name: f for f in fields}
    for name, field_spec in by_name.items():
        if name not in values and field_spec.default is None:
            continue
        value = values[name] if name in values else field_spec.default
        argv.extend(field_spec.emit(value))
    return argv
