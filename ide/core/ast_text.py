def ast_to_connected_text(ast_dict: dict) -> str:
    """Convierte el AST serializado en un árbol conectado con ubicaciones."""
    lines: list[str] = []

    def label_for(node: dict) -> str:
        label = node.get("label", node.get("type", "Nodo"))
        if "valor" in node:
            label = f"{label} ({node['valor']})"
        elif "nombre" in node:
            label = f"{label} ({node['nombre']})"

        linea = node.get("linea", 0)
        columna = node.get("columna", 0)
        ubicacion = f"[L{linea}:C{columna}]" if linea and columna else "[sin ubicación]"
        return f"{label} {ubicacion}"

    def walk(node: dict, prefix: str = "", is_last: bool = True, is_root: bool = True):
        connector = "" if is_root else ("`-- " if is_last else "|-- ")
        lines.append(f"{prefix}{connector}{label_for(node)}")
        children = [child for child in node.get("children", []) if child is not None]
        child_prefix = prefix if is_root else prefix + ("    " if is_last else "|   ")
        for index, child in enumerate(children):
            walk(child, child_prefix, index == len(children) - 1, False)

    walk(ast_dict)
    return "\n".join(lines) + "\n"
