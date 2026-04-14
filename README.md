# Visualizador de Grafos de Arquitetura

Ferramenta standalone para gerar e visualizar diagramas interativos de arquitetura de software.

Sem dependencias de framework, sem servidor obrigatorio. Funciona com um arquivo JSON e um browser.

---

## Como usar

### Opcao 1: Direto no browser (sem Python)

1. Abra o arquivo `viewer.html` no browser
2. Arraste um arquivo JSON ou cole o conteudo gerado pelo `generator.py`
3. O grafo renderiza imediatamente

### Opcao 2: Gerar JSON a partir de uma definicao

Defina sua arquitetura no formato descrito abaixo e rode:

```bash
python generator.py example/arch_definition.json -o meu_grafo.json
```

Depois abra o `viewer.html` e carregue o `meu_grafo.json`.

---

## Formato de entrada (arch_definition.json)

```json
{
  "project_name": "Nome do Projeto",
  "layers": [
    {
      "id": "layer_1",
      "name": "Nome da Camada",
      "description": "O que esta camada faz",
      "color": "#2563eb",
      "components": [
        {
          "name": "Nome do Componente",
          "tech": "Tecnologia",
          "type": "ui",
          "description": "O que este componente faz",
          "connections_to": ["Nome de outro componente em outra camada"]
        }
      ],
      "connections_to": ["layer_2"]
    }
  ]
}
```

**Tipos de componente:** `source`, `process`, `store`, `api`, `ui`, `infra`

**connections_to nos componentes:** use o nome exato de componentes em outras camadas que este alimenta ou chama. Se deixar vazio, o sistema infere as conexoes pelo tipo do componente.

---

## Formato de saida (compativel com viewer.html)

O `generator.py` produz um JSON com `nodes` e `edges` no formato Cytoscape.js.
Voce tambem pode montar este JSON manualmente e carregar direto no viewer.

```json
{
  "project_name": "string",
  "nodes": [...],
  "edges": [...]
}
```

---

## Funcionalidades do viewer

- Drag, pan e zoom livres
- Tooltip ao passar o mouse (nome, tecnologia, descricao)
- Layout automatico DAG da esquerda para direita
- Tres tipos de aresta: fluxo entre camadas, conexao entre componentes, pertencimento
- Botoes de zoom e ajuste de tela
- Carregar JSON via drag-and-drop, selector de arquivo ou colando no textarea
- Parametro de URL: `viewer.html?json=caminho/do/arquivo.json`

---

## Arquivos

| Arquivo                        | Descricao                                        |
|-------------------------------|--------------------------------------------------|
| `viewer.html`                  | Visualizador standalone (abrir no browser)       |
| `generator.py`                 | Converte definicao de arquitetura em JSON        |
| `example/arch_definition.json` | Exemplo de definicao com 4 camadas               |
| `requirements.txt`             | Dependencias opcionais (pyyaml para arquivos yml)|

---

**Autor:** Marcus Andrade
[linkedin.com/in/madrade](https://www.linkedin.com/in/madrade) | [github.com/madrade1472](https://github.com/madrade1472)
