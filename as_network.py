# %%
from functools import cache
from typing import Any, List, Iterable

import networkx as nx
import pandas as pd

import database_loader

files = database_loader.find_files(
    "./SnomedCT_InternationalRF2_PRODUCTION_20221231T120000Z/Full/Terminology/"
)
tables = {}
for file, path in files.items():
    tables[file] = pd.read_csv(path, sep="\t", header="infer")


@cache
def get_name(c: int) -> str:
    """Retrieve the name of a SNOMED concept."""
    d = tables["Description"].copy()
    t = d[
        (d["active"] == 1) & (d["typeId"] == 900000000000003001) & (d["conceptId"] == c)
    ]["term"]
    if t.empty:
        return c
    return t.values[0]


def find_common_ancestor(G: nx.DiGraph, targetNodes: List[Any]) -> Any:
    """Retrieves the common ancestor of more than only a pair of nodes."""
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
            return best_ancestor
    return best_ancestor


@cache
def graph_from_snomed() -> nx.DiGraph:
    """Loads a directed graph from SNOMED CT, using the relationships as a basis."""
    return nx.from_pandas_edgelist(
            tables["Relationship"].query("active == 1"), #TODO: it should actually be only edges of type 'is a'?
        source="destinationId",
        target="sourceId",
        edge_attr="typeId",
        create_using=nx.DiGraph(),
    )


def subgraph_on_nodes(G: nx.DiGraph, nodes: Iterable[Any]) -> nx.DiGraph:
    """Returns a subgraph of G, containing the nodes and all linked nodes."""
    parents = set(nodes)
    for n in nodes:
        parents = parents | nx.ancestors(G, n)
    return G.subgraph(parents)


def plot_graph_highlight_lca(
    G: nx.DiGraph, nodes: Iterable[Any], file_path: str
) -> None:
    """Plots a subgraph of G, highlighting the target nodes and its lowest common
    ancestor."""
    from pyvis.network import Network

    for i, layer in enumerate(nx.topological_generations(G)):
        for node in layer:
            if node in nodes:
                G.nodes[node]["group"] = "target"
            else:
                G.nodes[node]["group"] = "normal"
            G.nodes[node]["label"] = f"{get_name(node)}\n{node}"
            G.nodes[node]["level"] = i

    G.nodes[find_common_ancestor(G, gender)]["group"] = "type"
    pos = nx.multipartite_layout(G, subset_key="level", align="horizontal")
    nt = Network(directed=True, select_menu=True, filter_menu=True, layout=pos)
    nt.set_options(
        """
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
    """
    )
    nt.from_nx(G)
    nt.show(file_path)


# %%
G_snomed = graph_from_snomed()

# %% [markdown]
# Example with gender

# %%
gender = [248152002, 248153007, 32570681000036106, 261665006]
subG_snomed = subgraph_on_nodes(G_snomed, gender)

# %%
plot_graph_highlight_lca(subG_snomed, gender, "gender.html")

# %% [markdown]
# Example with Treatment Substances

# %%
substances = [
    391632007,
    108800000,
    764365009,
    715640009,
    108754007,
    108749003,
    108751004,
    108791001,
    414804006,
    763559000,
    787019001,
    703786007,
    871800005,
    444609007,
    74964007,
]
subG_subst = subgraph_on_nodes(G_snomed, substances[:-1])

# %%
a = find_common_ancestor(subG_subst, substances[:-1])
get_name(a)

# %%
plot_graph_highlight_lca(subG_subst, substances[:-1], "substances.html")
# %%
