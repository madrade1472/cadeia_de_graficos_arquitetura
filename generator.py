"""
Gerador de grafo interativo de arquitetura.

Converte uma definicao simples de arquitetura (JSON ou YAML) no formato
compativel com o viewer Cytoscape.js.

Uso:
    python generator.py input.json            -> imprime JSON no stdout
    python generator.py input.json -o out.json
    python generator.py input.json --serve    -> abre viewer no browser

Formato de entrada (input.json):
    {
      "project_name": "Meu Projeto",
      "layers": [
        {
          "id": "layer_1",
          "name": "Interface",
          "description": "Camada de apresentacao",
          "color": "#2563eb",
          "components": [
            {
              "name": "App Web",
              "tech": "React",
              "type": "ui",
              "description": "Frontend principal",
              "connections_to": ["API Gateway"]
            }
          ],
          "connections_to": ["layer_2"]
        }
      ]
    }

Tipos de componente validos:
    source, process, store, api, ui, infra
"""

import json
import re
import sys
import argparse
from pathlib import Path

# Cores padrao por indice de camada
DEFAULT_COLORS = [
    "#2563eb",
    "#16a34a",
    "#9333ea",
    "#ea580c",
    "#dc2626",
    "#0891b2",
    "#854d0e",
    "#475569",
]

# Tipos que "produzem" dados  vs  que "consomem"
_OUTPUT_TYPES = {"source", "api", "process"}
_INPUT_TYPES  = {"process", "store", "api"}


def _safe_id(text: str, prefix: str, index: int) -> str:
    slug = re.sub(r"[^a-z0-9]", "_", text.lower())[:14].strip("_")
    return f"{prefix}_{index}_{slug}"


def generate(arch: dict) -> dict:
    """
    Recebe o dict de arquitetura e retorna o dict Cytoscape.js
    com nodes e edges prontos para o viewer.
    """
    layers = arch.get("layers", [])
    project_name = arch.get("project_name", "Arquitetura")

    nodes: list[dict] = []
    edges: list[dict] = []
    edge_ids: set[str] = set()

    def _add_edge(src: str, tgt: str, etype: str, color: str) -> None:
        eid = f"e_{src}__{tgt}"
        if eid in edge_ids or src == tgt:
            return
        edge_ids.add(eid)
        edges.append({
            "data": {"id": eid, "source": src, "target": tgt,
                     "type": etype, "color": color},
            "classes": f"{etype}-edge",
        })

    # Passo 1: montar nodes + lookup nome -> id
    name_to_id: dict[str, str] = {}
    layer_color: dict[str, str] = {}
    comp_records: list[tuple] = []  # (lid, cid, comp, color)

    for i, layer in enumerate(layers):
        color = layer.get("color") or DEFAULT_COLORS[i % len(DEFAULT_COLORS)]
        lid = layer.get("id") or f"layer_{i+1}"
        layer_color[lid] = color

        nodes.append({
            "data": {
                "id": lid,
                "label": layer.get("name", lid),
                "type": "layer",
                "color": color,
                "description": layer.get("description", ""),
            },
            "classes": "layer-node",
        })

        for j, comp in enumerate(layer.get("components", [])):
            cid = _safe_id(comp.get("name", f"comp_{j}"), lid, j)
            name_to_id[comp.get("name", "").lower().strip()] = cid
            comp_records.append((lid, cid, comp, color))

            nodes.append({
                "data": {
                    "id": cid,
                    "label": comp.get("name", ""),
                    "tech": comp.get("tech", ""),
                    "comp_type": comp.get("type", "process"),
                    "type": "component",
                    "color": color,
                    "parent_layer": lid,
                    "description": comp.get("description", ""),
                },
                "classes": "comp-node",
            })

    # Passo 2: edges de pertencimento (layer -> comp, dashed)
    for lid, cid, comp, color in comp_records:
        _add_edge(lid, cid, "member", color)

    # Passo 3: edges de fluxo entre camadas
    layer_ids = [l.get("id") or f"layer_{i+1}" for i, l in enumerate(layers)]
    connected_layers: set[tuple] = set()

    for i, layer in enumerate(layers):
        lid = layer_ids[i]
        targets = layer.get("connections_to", [])
        if targets:
            for tid in targets:
                if tid in layer_color:
                    _add_edge(lid, tid, "flow", layer_color[lid])
                    connected_layers.add((lid, tid))
        else:
            if i > 0:
                prev = layer_ids[i - 1]
                _add_edge(prev, lid, "flow", layer_color[lid])
                connected_layers.add((prev, lid))

    # Passo 4: edges comp -> comp vindos da definicao
    has_comp_connections = False
    for lid, cid, comp, color in comp_records:
        for target_name in comp.get("connections_to", []):
            target_id = name_to_id.get(target_name.lower().strip())
            if target_id and target_id != cid:
                _add_edge(cid, target_id, "comp-flow", color)
                has_comp_connections = True

    # Passo 5: fallback por tipo quando nao ha conexoes explicitas
    if not has_comp_connections:
        by_layer: dict[str, list] = {}
        for lid, cid, comp, color in comp_records:
            by_layer.setdefault(lid, []).append((cid, comp, color))

        for src_lid, tgt_lid in connected_layers:
            src_comps = by_layer.get(src_lid, [])
            tgt_comps = by_layer.get(tgt_lid, [])
            if not src_comps or not tgt_comps:
                continue

            src_cands = [(c, co, cl) for c, co, cl in src_comps
                         if co.get("type", "process") in _OUTPUT_TYPES] or src_comps[:1]
            tgt_cands = [(c, co, cl) for c, co, cl in tgt_comps
                         if co.get("type", "process") in _INPUT_TYPES] or tgt_comps[:1]

            for s_cid, _, s_col in src_cands[:2]:
                for t_cid, _, _ in tgt_cands[:2]:
                    _add_edge(s_cid, t_cid, "comp-flow", s_col)

    return {"nodes": nodes, "edges": edges, "project_name": project_name}


def load_input(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"Erro: arquivo nao encontrado: {path}", file=sys.stderr)
        sys.exit(1)

    text = p.read_text(encoding="utf-8")

    if p.suffix in (".yaml", ".yml"):
        try:
            import yaml
            return yaml.safe_load(text)
        except ImportError:
            print("Erro: instale pyyaml para usar arquivos YAML (pip install pyyaml)", file=sys.stderr)
            sys.exit(1)

    return json.loads(text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera JSON de grafo interativo a partir de definicao de arquitetura"
    )
    parser.add_argument("input", help="Arquivo JSON ou YAML com a definicao da arquitetura")
    parser.add_argument("-o", "--output", help="Salvar resultado em arquivo (default: stdout)")
    parser.add_argument("--serve", action="store_true",
                        help="Abrir viewer.html no browser apos gerar")
    args = parser.parse_args()

    arch = load_input(args.input)
    graph = generate(arch)
    out_json = json.dumps(graph, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(out_json, encoding="utf-8")
        print(f"Salvo em: {args.output}")
    else:
        print(out_json)

    if args.serve:
        import webbrowser
        viewer = Path(__file__).parent / "viewer.html"
        if viewer.exists():
            webbrowser.open(viewer.as_uri())
        else:
            print("viewer.html nao encontrado no mesmo diretorio.", file=sys.stderr)


if __name__ == "__main__":
    main()
