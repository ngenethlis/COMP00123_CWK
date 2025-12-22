import networkx as nx
import matplotlib.pyplot as plt

def load_network(filepath):
    """
    Loads a network from a KONECT/SNAP edge list file.
    """
    # Read the edge list. 
    # 'comments' parameter skips lines starting with % or #
    # 'create_using=nx.DiGraph()' ensures it's a Directed Graph (important for software!)
    G = nx.read_edgelist(filepath, comments='%', nodetype=int, create_using=nx.DiGraph())
    
    # Remove self-loops (files including themselves) as they often mess up calculations
    G.remove_edges_from(nx.selfloop_edges(G))
    
    return G

# --- MAIN EXECUTION ---

def main():
    path_linux = "data/linux/out.linux"
    G_linux = load_network(path_linux)
    print(f"Linux Kernel: {G_linux.number_of_nodes()} nodes, {G_linux.number_of_edges()} edges")

    # 2. Load Java (JDK)
    # Replace 'out.jdk' with your actual filename
    path_java = "data/subelj_jdk/out.subelj_jdk_jdk"
    G_java = load_network(path_java)
    print(f"Java JDK:     {G_java.number_of_nodes()} nodes, {G_java.number_of_edges()} edges")

    # --- BASIC FEASIBILITY CHECK ---

    # If the networks are too big (>50k nodes), print a warning
    if G_linux.number_of_nodes() > 50000:
        print("WARNING: Linux network is too large for this coursework. Consider a subgraph.")

    # Check for 'God Classes' (Hubs) - top 5 most connected files
    print("\nTop 5 Hubs in Linux (Out-Degree - files that include many others):")
    print(sorted(G_linux.out_degree, key=lambda x: x[1], reverse=True)[:5])

    print("\nTop 5 Hubs in Java (Out-Degree - classes that import many others):")
    print(sorted(G_java.out_degree, key=lambda x: x[1], reverse=True)[:5])


main()
