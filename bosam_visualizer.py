import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def draw_bosam(edge_list_file, fname):
    G = nx.Graph()

    with open(edge_list_file, 'r') as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith('%') or line.startswith('#'):
                continue

            parts = line.split()

            if len(parts) >= 2:
                u, v = parts[0], parts[1]
                G.add_edge(u, v)

    data = []

    degrees = dict(G.degree())

    for node in G.nodes():
        neighbors = list(G.neighbors(node))

        k = degrees[node]

        if neighbors:
            w = max(degrees[nb] for nb in neighbors)

            e = max(nb for nb in neighbors)
        else:
            w = -1
            e = -1

        data.append({
            'node': node,
            'k': k,
            'w': w,
            'e': e
        })

    df = pd.DataFrame(data)
    df_sorted = df.sort_values(by=['k', 'w', 'e'], ascending=[True, True, True])

    sorted_node_order = df_sorted['node'].tolist()

    adj_matrix = nx.to_scipy_sparse_array(G, nodelist=sorted_node_order, format='csr')

    plt.figure(figsize=(12, 12))

    plt.spy(adj_matrix, markersize=0.1, color='black')

    plt.title(f"BOSAM for {fname}, ({G.number_of_nodes()} nodes)")
    plt.xlabel("Node Index (Sorted)")
    plt.ylabel("Node Index (Sorted)")

    fname = f"bosam_{fname.replace(' ', '_')}.png"
    plt.savefig(fname, dpi=600) 

def bosam_linux():
    f_linux = "data/linux/out.linux"
    draw_bosam(f_linux,"Linux Kernel")

def bosam_jdk():
    f_jdk = "data/subelj_jdk/out.subelj_jdk_jdk"
    draw_bosam(f_jdk,"JDK")

bosam_linux()
bosam_jdk()
