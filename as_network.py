# %%
import pandas as pd

import database_loader

files = database_loader.find_files(
    "./SnomedCT_InternationalRF2_PRODUCTION_20221231T120000Z/Full/Terminology/"
)
tables = {}
for file, path in files.items():
    tables[file] = pd.read_csv(path, sep="\t", header="infer")


# %%
def get_name(c: int, d: pd.DataFrame) -> str:
    t = d[
        (d["active"] == 1)
        & (d["typeId"] == 900000000000003001)
        & (d["conceptId"] == c)
    ]["term"]
    if t.empty:
        return c
    return t.values[0]


# %%
import networkx as nx

G = nx.from_pandas_edgelist(
    tables["Relationship"].query("active == 1"),
    source="destinationId",
    target="sourceId",
    edge_attr="typeId",
    create_using=nx.DiGraph(),
)

# %%
from typing import Any, List


def find_common_ancestor(G: nx.DiGraph, targetNodes: List[Any]) -> Any:
    topology = nx.topological_generations(G)
    best_ancestor = None
    for generation, nodes in enumerate(topology):
        generation_links = False
        for node_i, node in enumerate(nodes):
            links_to_all = True
            for target in targetNodes:
                if not nx.has_path(G, node, target):
                    links_to_all = False
            if links_to_all:
                generation_links = True
                best_ancestor = node
        if not generation_links:
            break
    return best_ancestor

# %%

gender = [248152002, 248153007, 32570681000036106, 261665006]
parents = {138875005} | set(gender)
for gen in gender:
    parents = parents | nx.ancestors(G, gen)

subG = G.subgraph(parents)

# %%
# plotting
from pyvis.network import Network

for i, layer in enumerate(nx.topological_generations(subG)):
    for node in layer:
        if node in gender[:-1]:
            subG.nodes[node]["group"] = "target"
        else:
            subG.nodes[node]["group"] = "normal"
        subG.nodes[node]["label"] = f'{get_name(node, tables["Description"])}\n{node}'
        subG.nodes[node]["level"] = i

subG.nodes[find_common_ancestor(subG, gender[:-1])]["group"] = "type"

pos = nx.multipartite_layout(subG, subset_key="layer", align="horizontal", scale=25)
nt = Network(directed=True, select_menu=True, filter_menu=True, layout=pos)
nt.show_buttons()
nt.set_options("""
var options = {
    "configure": {
        "enabled": true
    },
    "groups": {
        "normal": {"color": {"background": "#97c3fc", "border": "#4c617f"}},
        "target": {"color": {"background": "#c3fc97", "border": "#617f4c"}},
        "type": {"color": {"background": "#fc97c3", "border": "#7f4c61"}}
    },
    "edges": {
        "color": {
            "inherit": true
        },
        "smooth": {
            "enabled": true,
            "type": "dynamic"
        }
    },
    "interaction": {
        "dragNodes": true,
        "hideEdgesOnDrag": false,
        "hideNodesOnDrag": false
    },
    "layout": {
        "hierarchical": {
            "blockShifting": true,
            "edgeMinimization": true,
            "enabled": true,
            "levelSeparation": 125,
            "parentCentralization": true,
            "sortMethod": "hubsize",
            "treeSpacing": 200
        },
        "improvedLayout": true,
        "randomSeed": 0
    },
    "physics": {
        "enabled": true,
        "stabilization": {
            "enabled": true,
            "fit": true,
            "iterations": 1000,
            "onlyDynamicEdges": false,
            "updateInterval": 50
        },
        "hierarchicalRepulsion": {
            "nodeDistance": 150
        }
    }
}
""")
nt.from_nx(subG)
nt.show('gender.html')

# %%


find_common_ancestor(subG, gender[:-1])

# %%

pos = nx.multipartite_layout(subG, subset_key="layer", align="horizontal", scale=25)
nt = Network(directed=True, select_menu=True, filter_menu=True, layout=pos)
nt.from_nx(subG)
nt.show('gender.html')
# %%
