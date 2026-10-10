"""Tree-sitter backend: semantic chunking for non-Python languages.

Optional: requires the `treesitter` extra (tree-sitter + tree-sitter-language-pack).
If the grammars are not installed, importing this module raises ImportError and the
registry keeps Python-only support — the core stays dependency-free.

Each language is described by a LangSpec and chunked by one generic, container-aware
walker. Containers (namespaces, modules, declaration lists) are recursed into so that
nested declarations are found at any depth; classes are not recursed into, because
their methods are handled explicitly against the class.
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

# Node types that carry an entity's name, tried when there is no explicit `name` field.
_NAME_TYPES = frozenset({
    "identifier", "type_identifier", "property_identifier", "field_identifier",
    "simple_identifier", "name", "constant", "scoped_identifier",
})
# C/C++ declarator wrappers to descend through to reach the real name.
_DECLARATOR_TYPES = frozenset({
    "function_declarator", "pointer_declarator", "reference_declarator",
    "init_declarator", "parenthesized_declarator", "array_declarator",
})
# Bodies that hold a class's members, when there is no explicit `body` field.
_BODY_TYPES = frozenset({
    "field_declaration_list", "declaration_list", "class_body",
    "body_statement", "block", "enum_variant_list",
})


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
    # Node types to recurse into (namespaces, modules, declaration lists).
    container_types: frozenset[str] = field(default_factory=frozenset)
    # Optional per-node-type override for a class-like node's chunk kind.
    class_kind: dict[str, str] = field(default_factory=dict)
    # Optional per-node-type override for a member (method-body) chunk kind.
    member_kind: dict[str, str] = field(default_factory=dict)


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
    LangSpec(
        language="rust",
        grammar="rust",
        extensions=(".rs",),
        func_types=frozenset({"function_item"}),
        class_types=frozenset({"impl_item"}),
        method_types=frozenset({"function_item"}),
        other={"struct_item": "struct", "enum_item": "enum", "trait_item": "trait"},
        import_types=frozenset({"use_declaration"}),
    ),
    LangSpec(
        language="java",
        grammar="java",
        extensions=(".java",),
        func_types=frozenset(),
        class_types=frozenset({
            "class_declaration",
            "interface_declaration",
            "enum_declaration",
            "record_declaration",
        }),
        method_types=frozenset({"method_declaration", "constructor_declaration"}),
        import_types=frozenset({"import_declaration"}),
    ),
    # --- v2.0 languages ---------------------------------------------------
    LangSpec(
        language="c",
        grammar="c",
        extensions=(".c", ".h"),
        func_types=frozenset({"function_definition"}),
        class_types=frozenset(),
        method_types=frozenset(),
        other={
            "struct_specifier": "struct",
            "enum_specifier": "enum",
            "union_specifier": "union",
            "type_definition": "type",
        },
        import_types=frozenset({"preproc_include"}),
    ),
    LangSpec(
        language="cpp",
        grammar="cpp",
        extensions=(".cpp", ".cc", ".cxx", ".hpp", ".hh"),
        func_types=frozenset({"function_definition"}),
        class_types=frozenset({"class_specifier", "struct_specifier"}),
        method_types=frozenset({"function_definition"}),
        other={"enum_specifier": "enum"},
        import_types=frozenset({"preproc_include"}),
        container_types=frozenset({
            "namespace_definition", "declaration_list", "linkage_specification",
        }),
        class_kind={"class_specifier": "class", "struct_specifier": "struct"},
    ),
    LangSpec(
        language="csharp",
        grammar="csharp",
        extensions=(".cs",),
        func_types=frozenset(),
        class_types=frozenset({
            "class_declaration", "interface_declaration", "struct_declaration",
            "enum_declaration", "record_declaration",
        }),
        method_types=frozenset({
            "method_declaration", "constructor_declaration", "property_declaration",
        }),
        import_types=frozenset({"using_directive"}),
        container_types=frozenset({
            "namespace_declaration", "file_scoped_namespace_declaration", "declaration_list",
        }),
        class_kind={
            "interface_declaration": "interface", "struct_declaration": "struct",
            "enum_declaration": "enum", "record_declaration": "record",
        },
        member_kind={"property_declaration": "property"},
    ),
    LangSpec(
        language="ruby",
        grammar="ruby",
        extensions=(".rb",),
        func_types=frozenset({"method", "singleton_method"}),
        class_types=frozenset({"class"}),
        method_types=frozenset({"method", "singleton_method"}),
        container_types=frozenset({"module", "body_statement"}),
    ),
    LangSpec(
        language="php",
        grammar="php",
        extensions=(".php",),
        func_types=frozenset({"function_definition"}),
        class_types=frozenset({
            "class_declaration", "interface_declaration", "trait_declaration",
        }),
        method_types=frozenset({"method_declaration"}),
        import_types=frozenset({"namespace_use_declaration"}),
        container_types=frozenset({"namespace_definition", "declaration_list"}),
        class_kind={
            "interface_declaration": "interface", "trait_declaration": "trait",
        },
    ),
    LangSpec(
        language="kotlin",
        grammar="kotlin",
        extensions=(".kt", ".kts"),
        func_types=frozenset({"function_declaration"}),
        class_types=frozenset({"class_declaration"}),
        method_types=frozenset({"function_declaration"}),
        import_types=frozenset({"import_list"}),
    ),
)


def _text(node: Any) -> str:
    return node.text.decode("utf-8", "replace")


def _name(node: Any) -> str | None:
    named = node.child_by_field_name("name")
    if named is not None:
        return _text(named)
    decl = node.child_by_field_name("declarator")
    while decl is not None and decl.type in _DECLARATOR_TYPES:
        decl = decl.child_by_field_name("declarator")
    if decl is not None and decl.type in _NAME_TYPES:
        return _text(decl)
    for child in node.named_children:
        if child.type in _NAME_TYPES:
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
            self._walk(node, imports, chunks)
        return chunks

    def _walk(self, node: Any, imports: tuple[str, ...], out: list[Chunk]) -> None:
        spec = self._spec
        node_type = node.type
        if node_type in spec.class_types:
            self._emit_class(node, imports, out)
        elif node_type in spec.func_types:
            out.append(self._chunk("function", node, _name(node), imports, None))
        elif node_type in spec.other:
            self._emit_other(node, imports, out)
        elif node_type in spec.container_types:
            for child in node.named_children:
                self._walk(child, imports, out)

    def _emit_class(self, node: Any, imports: tuple[str, ...], out: list[Chunk]) -> None:
        spec = self._spec
        name = _name(node)
        kind = spec.class_kind.get(node.type, "class")
        out.append(self._chunk(kind, node, name, imports, None))
        body = self._body(node)
        if body is not None:
            for sub in body.named_children:
                if sub.type in spec.method_types:
                    member = spec.member_kind.get(sub.type, "method")
                    out.append(self._chunk(member, sub, _name(sub), imports, name))

    def _emit_other(self, node: Any, imports: tuple[str, ...], out: list[Chunk]) -> None:
        spec = self._spec
        kind = spec.other[node.type]
        type_specs = [c for c in node.named_children if c.type == "type_spec"]
        if type_specs:
            for spec_node in type_specs:
                out.append(self._chunk("type", spec_node, _name(spec_node), imports, None))
        else:
            out.append(self._chunk(kind, node, _name(node), imports, None))

    @staticmethod
    def _body(node: Any) -> Any:
        body = node.child_by_field_name("body")
        if body is not None:
            return body
        for child in node.named_children:
            if child.type in _BODY_TYPES:
                return child
        return None

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


def register_tree_sitter(register: Callable[[Parser], None]) -> None:
    """Register a TreeSitterParser for every supported language."""
    for spec in SPECS:
        register(TreeSitterParser(spec))