"""Tree-sitter backend: semantic chunking for non-Python languages.

Optional: requires the `treesitter` extra (tree-sitter + tree-sitter-language-pack).
If the grammars are not installed, importing this module raises ImportError and the
registry keeps Python-only support â€” the core stays dependency-free.

Each language is described by a LangSpec and chunked by one generic walker.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from tree_sitter_language_pack import get_parser

from .base import Parser
from .models import Chunk

_JS_FUNCS = frozenset({"function_declaration", "generator_function_declaration"})
_TS_METHODS = frozenset({"method_definition", "method_signature", "abstract_method_signature"})
_TS_CLASSES = frozenset({"class_declaration", "abstract_class_declaration"})
_TS_OTHER = {
    "interface_declaration": "interface",
    "type_alias_declaration": "type",
    "enum_declaration": "enum",
}


@dataclass(frozen=True)
class LangSpec:
    """How one tree-sitter grammar maps node types to chunk kinds."""

    language: str
    grammar: str
    extensions: tuple[str, ...]
    func_types: frozenset[str]
    class_types: frozenset[str]
    method_types: frozenset[str]
    other: dict[str, str] = field(default_factory=dict)
    import_types: frozenset[str] = field(default_factory=frozenset)


SPECS: tuple[LangSpec, ...] = (
    LangSpec(
        language="javascript",
        grammar="javascript",
        extensions=(".js", ".jsx", ".mjs", ".cjs"),
        func_types=_JS_FUNCS,
        class_types=frozenset({"class_declaration"}),
        method_types=frozenset({"method_definition"}),
        import_types=frozenset({"import_statement"}),
    ),
    LangSpec(
        language="typescript",
        grammar="typescript",
        extensions=(".ts",),
        func_types=_JS_FUNCS,
        class_types=_TS_CLASSES,
        method_types=_TS_METHODS,
        other=_TS_OTHER,
        import_types=frozenset({"import_statement"}),
    ),
    LangSpec(
        language="tsx",
        grammar="tsx",
        extensions=(".tsx",),
        func_types=_JS_FUNCS,
        class_types=_TS_CLASSES,
        method_types=_TS_METHODS,
        other=_TS_OTHER,
        import_types=frozenset({"import_statement"}),
    ),
    LangSpec(
        language="go",
        grammar="go",
        extensions=(".go",),
        func_types=frozenset({"function_declaration"}),
        class_types=frozenset(),
        method_types=frozenset(),
        other={"method_declaration": "method", "type_declaration": "type"},
        import_types=frozenset({"import_declaration"}),
    ),
)


def _text(node: Any) -> str:
    return node.text.decode("utf-8", "replace")


def _name(node: Any) -> str | None:
    named = node.child_by_field_name("name")
    if named is not None:
        return _text(named)
    for child in node.named_children:
        if child.type in ("identifier", "type_identifier", "property_identifier"):
            return _text(child)
    return None


class TreeSitterParser:
    """Parser for one tree-sitter language, implementing the Parser protocol."""

    def __init__(self, spec: LangSpec) -> None:
        self._spec = spec
        self.language: str = spec.language
        self.extensions: tuple[str, ...] = spec.extensions
        self._parser = get_parser(spec.grammar)

    def parse(self, path: str, source: str) -> list[Chunk]:
        tree = self._parser.parse(source.encode("utf-8", "replace"))
        root = tree.root_node
        spec = self._spec
        imports = tuple(
            _text(n).strip() for n in root.named_children if n.type in spec.import_types
        )
        chunks: list[Chunk] = []
        for node in root.named_children:
            self._emit(node, imports, chunks)
        return chunks

    def _emit(self, node: Any, imports: tuple[str, ...], out: list[Chunk]) -> None:
        spec = self._spec
        node_type = node.type
        if node_type in spec.func_types:
            out.append(self._chunk("function", node, _name(node), imports, None))
        elif node_type in spec.class_types:
            name = _name(node)
            out.append(self._chunk("class", node, name, imports, None))
            body = node.child_by_field_name("body")
            if body is not None:
                for sub in body.named_children:
                    if sub.type in spec.method_types:
                        out.append(self._chunk("method", sub, _name(sub), imports, name))
        elif node_type in spec.other:
            kind = spec.other[node_type]
            type_specs = [c for c in node.named_children if c.type == "type_spec"]
            if type_specs:
                for spec_node in type_specs:
                    out.append(self._chunk("type", spec_node, _name(spec_node), imports, None))
            else:
                out.append(self._chunk(kind, node, _name(node), imports, None))

    def _chunk(
        self,
        kind: str,
        node: Any,
        name: str | None,
        imports: tuple[str, ...],
        parent: str | None,
    ) -> Chunk:
        return Chunk(
            path="",
            language=self._spec.language,
            kind=kind,
            name=name or "<anonymous>",
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            text=_text(node),
            parent=parent,
            imports=imports,
        )

    def parse_path(self, path: str, source: str) -> list[Chunk]:
        return [
            Chunk(
                path=path,
                language=c.language,
                kind=c.kind,
                name=c.name,
                start_line=c.start_line,
                end_line=c.end_line,
                text=c.text,
                parent=c.parent,
                imports=c.imports,
            )
            for c in self.parse(path, source)
        ]


def register_tree_sitter(register: Callable[[Parser], None]) -> None:
    """Register a TreeSitterParser for every supported language."""
    for spec in SPECS:
        register(TreeSitterParser(spec))