# `tafsirkg.tei`: reading the TEI files

This layer turns the TEI XML into a typed node tree and knows nothing about the ontology or RDF.

| File | What it does |
|---|---|
| `model.py` | One frozen dataclass per TEI element (`Division`, `Paragraph`, `Quote`, `PersName`, …). Each node keeps its typed attributes, all raw `attributes`, its `source` (file and line) and its mixed content in order (`children` holds both elements and text). Unknown tags become `UnknownElement`, so their content is never lost. Nodes compare by identity. |
| `reader.py` | `TeiReader` parses a file with lxml and builds the tree below `<text>/<body>`. A registry (`_FACTORIES`) maps each tag to the function that builds its node. A file that is not well-formed TEI, or not in the TEI namespace, raises `TeiFormatError` and logs an error. |
| `visitor.py` | `TeiVisitor` sends each node to `visit_<ClassName>`. Anything not overridden falls back to `generic_visit`, which visits the children. |
| `text.py` | `plain_text(node)` returns the readable text, with whitespace collapsed and `<note>` content left out. |
| `inventory.py` | `TeiInventory` counts elements, parent > child nesting and attribute values. The CLI command `tafsirkg inventory` uses it. |

To support a new TEI element, add a class in `model.py` and a factory in `reader.py`. Then handle it in `mapping/inline.py`, or in `mapping/document.py` if it is a structural element.
