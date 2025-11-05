import ast
import os
import re
from pathlib import Path
from typing import List, Tuple, Dict

SRC_DIR = Path("src")
DOCS_DIR = Path("docs")
JAC_FILE = Path("Assignment2.jac")

SRC_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)

def parse_python(content: str) -> List[Tuple[str, str]]:
    items = []
    try:
        module = ast.parse(content)
    except Exception:
        return parse_generic_comments(content)
    module_doc = ast.get_docstring(module)
    if module_doc:
        items.append(("module", module_doc.strip()))
    for node in module.body:
        if isinstance(node, ast.FunctionDef):
            name = node.name
            doc = ast.get_docstring(node) or ""
            title = f"def {name}()"
            items.append((title, doc.strip()))
        elif isinstance(node, ast.AsyncFunctionDef):
            name = node.name
            doc = ast.get_docstring(node) or ""
            title = f"async def {name}()"
            items.append((title, doc.strip()))
        elif isinstance(node, ast.ClassDef):
            name = node.name
            doc = ast.get_docstring(node) or ""
            methods = []
            for elt in node.body:
                if isinstance(elt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    mname = elt.name
                    mdoc = ast.get_docstring(elt) or ""
                    methods.append((mname, mdoc.strip()))
            body_lines = doc.strip()
            if methods:
                body_lines += "\n\nMethods:\n"
                for mname, mdoc in methods:
                    body_lines += f"- {mname}(): {mdoc or '(no doc)'}\n"
            items.append((f"class {name}", body_lines.strip() or "(no doc)"))
    return items

def parse_generic_comments(content: str) -> List[Tuple[str, str]]:
    items = []
    cblock_re = re.compile(r"/\*(.*?)\*/", re.DOTALL)
    for m in cblock_re.finditer(content):
        snippet = m.group(1).strip()
        if snippet:
            items.append(("comment_block", snippet))
    lines = content.splitlines()
    buff = []
    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith("//"):
            buff.append(stripped[2:].strip())
        elif stripped.startswith("#"):
            buff.append(stripped[1:].strip())
        else:
            if buff:
                items.append(("comment_block", "\n".join(buff).strip()))
                buff = []
    if buff:
        items.append(("comment_block", "\n".join(buff).strip()))
    return items

class Node:
    def __init__(self, j_type: str, **props):
        self.j_type = j_type
        self.props = props
        self.id = id(self)

class Edge:
    def __init__(self, j_type: str, src: Node, dst: Node):
        self.j_type = j_type
        self.source = src
        self.dest = dst

class GraphSimple:
    def __init__(self):
        self.nodes: List[Node] = []
        self.edges: List[Edge] = []
    def add_node(self, j_type: str, **props) -> Node:
        n = Node(j_type, **props)
        self.nodes.append(n)
        return n
    def add_edge(self, j_type: str, src: Node, dst: Node) -> Edge:
        e = Edge(j_type, src, dst)
        self.edges.append(e)
        return e
    def find_nodes(self, j_type: str) -> List[Node]:
        return [n for n in self.nodes if n.j_type == j_type]

USE_JASECI = False
try:
    from jaclang.lib.runtime import Runtime
    USE_JASECI = True
except Exception:
    USE_JASECI = False

def maybe_create_jaseci_nodes(js_runtime, node_data: Dict):
    try:
        if hasattr(js_runtime, "create_node"):
            return js_runtime.create_node(**node_data)
    except Exception:
        pass
    return None

def main():
    g = GraphSimple()
    js_runtime = None
    if USE_JASECI:
        try:
            js_runtime = Runtime()
            print("Jac/Jaseci runtime detected and initialized.")
        except Exception as e:
            print("Jac runtime initialization failed:", e)
            js_runtime = None
    file_paths = []
    for root, _, files in os.walk(SRC_DIR):
        for fn in files:
            if fn.lower().endswith((".py", ".js", ".java", ".ts", ".cpp", ".c", ".h")):
                p = Path(root) / fn
                file_paths.append(p)
    if not file_paths:
        print(f"No source files found in {SRC_DIR}.")
        return
    for path in file_paths:
        content = path.read_text(encoding="utf-8", errors="ignore")
        file_node = g.add_node("file", path=str(path), content=content)
        if js_runtime:
            try:
                maybe_create_jaseci_nodes(js_runtime, {"j_type": "file", "path": str(path), "content": content})
            except Exception:
                pass
        if path.suffix == ".py":
            items = parse_python(content)
        else:
            items = parse_generic_comments(content)
        if not items:
            items = [("Summary", f"No docstrings or comment blocks found in {path.name}")]
        for title, body in items:
            doc_node = g.add_node("doc", title=title, body=body or "(no description)", lang=path.suffix.lstrip("."))
            g.add_edge("for_file", doc_node, file_node)
            if js_runtime:
                try:
                    maybe_create_jaseci_nodes(js_runtime, {"j_type": "doc", "title": title, "body": body or "(no description)", "lang": path.suffix.lstrip(".")})
                except Exception:
                    pass
    if JAC_FILE.exists() and js_runtime:
        try:
            with open(JAC_FILE, "r", encoding="utf-8") as jf:
                jac_source = jf.read()
            if hasattr(js_runtime, "load_jac"):
                js_runtime.load_jac(jac_source)
            elif hasattr(js_runtime, "load_module"):
                js_runtime.load_module(jac_source)
            if hasattr(js_runtime, "run_walker"):
                js_runtime.run_walker("docger")
            print("Ran Jac walker 'docger'.")
        except Exception as e:
            print("Jac walker run failed:", e)
    for file_node in g.find_nodes("file"):
        linked_docs = [e.source for e in g.edges if e.j_type == "for_file" and e.dest is file_node]
        lines = []
        lines.append(f"# {Path(file_node.props['path']).name}\n")
        lines.append(f"_path_: `{file_node.props['path']}`\n")
        if not linked_docs:
            lines.append("No extracted docs found.\n")
        else:
            for doc in linked_docs:
                lines.append(f"## {doc.props.get('title','')}\n")
                body = doc.props.get("body", "(no description)")
                lines.append(body + "\n")
        out = DOCS_DIR / (Path(file_node.props['path']).name + ".md")
        out.write_text("\n".join(lines), encoding="utf-8")
        print(f"Wrote {out}")
    print("Done. Check the docs folder.")

if __name__ == "__main__":
    main()
