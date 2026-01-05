import networkx as nx
import matplotlib.pyplot as plt
import random
import argparse
import os

OUTPUT_DIR = "graphs"

class AttackSimulator:
    """
    Optimized Simulator: Removes expensive Diameter calc and avoids Graph copying.
    """
    def __init__(self, graph):
        self.graph = graph.copy()
        self.initial_size = len(self.graph)
        self.initial_gc_size = self.get_gc_size_only(self.graph)

    def get_gc_size_only(self, G):
        """Calculates Giant Component size WITHOUT creating a subgraph copy."""
        if len(G) == 0: return 0

        if G.is_directed():
            components = nx.weakly_connected_components(G)
        else:
            components = nx.connected_components(G)

        try:
            return max(len(c) for c in components)
        except ValueError:
            return 0

    def simulate(self, strategy="random", steps=50):
        print(f"   -> Simulating strategy: {strategy}...")
        G = self.graph.copy()
        N = len(G)

        if strategy == "random":
            nodes = list(G.nodes())
            random.shuffle(nodes)
        elif strategy == "degree":
            nodes = sorted(G.nodes(), key=lambda n: G.degree(n), reverse=True)
        elif strategy == "indegree":
            nodes = sorted(G.nodes(), key=lambda n: G.in_degree(n), reverse=True)
        elif "betweenness" in strategy:
            # Ensure k isn't larger than N
            k = 1000 if "approx" in strategy else None
            if k and k > N: k = N 

            print(f"      (Calculating Betweenness k={k}...)")
            bc = nx.betweenness_centrality(G, k=k)
            nodes = sorted(bc, key=bc.get, reverse=True)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        chunk = max(1, int(N / steps))
        res = {'x': [0.0], 'gc': [1.0], 'frag': []} 

        res['frag'].append(
            nx.number_weakly_connected_components(G) if G.is_directed() 
            else nx.number_connected_components(G)
        )

        removed_count = 0

        for _ in range(steps):
            if removed_count >= N: break

            batch = nodes[removed_count : removed_count + chunk]
            G.remove_nodes_from(batch)
            removed_count += len(batch)

            gc_sz = self.get_gc_size_only(G)

            frag = (nx.number_weakly_connected_components(G) 
                    if G.is_directed() 
                    else nx.number_connected_components(G))


            res['x'].append(removed_count / self.initial_size)
            res['gc'].append(gc_sz / self.initial_gc_size)
            res['frag'].append(frag)

            if gc_sz == 0: break

        return res


def plot_all_strategies(name, strategies_data, metric, ylabel, title_suffix):
    """Plots all strategies (Degree, Random, etc.) on a single graph for one network."""
    plt.figure(figsize=(10, 7))
    styles = {
        "random": ("green", "--", None),
        "degree": ("blue", "-", "o"),
        "indegree": ("red", "-", "s"),
        "betweenness_approx": ("purple", "-", "^")
    }

    for strategy, data in strategies_data.items():
        c, ls, m = styles.get(strategy, ("black", "-", None))
        x, y = data['x'], data[metric]
        min_len = min(len(x), len(y))
        plt.plot(x[:min_len], y[:min_len], color=c, linestyle=ls, marker=m, 
                 markevery=0.1, label=strategy, linewidth=2, alpha=0.8)

    if metric == 'gc':

        plt.axhline(y=0.25, color="red", linestyle=":", label="25% Threshold")
        plt.axhline(y=0.5, color="red", linestyle=":", label="50% Threshold")
        plt.axhline(y=0.75, color="red", linestyle=":", label="75% Threshold")

    plt.title(f"{name}: {title_suffix}")
    plt.xlabel("Fraction Removed")
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True, alpha=0.3)

    fname = os.path.join(OUTPUT_DIR, f"{name.replace(' ', '_')}_ALL_{metric}.png")
    plt.savefig(fname)
    plt.close()
    print(f"Saved: {fname}")

def plot_vs_random(name, real_res, rand_res, attack):
    """Plots Real vs Random for a SINGLE attack type."""
    plt.figure(figsize=(10, 6))

    plt.plot(real_res['x'], real_res['gc'], "b-", linewidth=2, label=f"{name} (Real)")
    plt.plot(rand_res['x'], rand_res['gc'], "r--", linewidth=2, label="Erdős-Rényi (Random)")

    plt.axhline(y=0.25, color="gray", linestyle=":", alpha=0.5)
    plt.axhline(y=0.5, color="gray", linestyle=":", alpha=0.5)
    plt.axhline(y=0.75, color="gray", linestyle=":", alpha=0.5)


    plt.title(f"Real vs Random: {name} ({attack})")
    plt.xlabel("Fraction Removed")
    plt.ylabel("Giant Component Fraction")
    plt.legend()
    plt.grid(True, alpha=0.3)

    fname = os.path.join(OUTPUT_DIR,f"{name.replace(' ', '_')}_VS_RANDOM_{attack}.png")
    plt.savefig(fname)
    plt.close()
    print(f"Saved: {fname}")

def plot_comparison(res1, name1, res2, name2, attack):
    """Plots Network A vs Network B for a SINGLE attack type."""
    if attack not in res1 or attack not in res2: return

    plt.figure(figsize=(10, 6))
    plt.plot(res1[attack]['x'], res1[attack]['gc'], "b-o", markevery=0.1, label=name1)
    plt.plot(res2[attack]['x'], res2[attack]['gc'], "r-s", markevery=0.1, label=name2)

    plt.axhline(y=0.25, color="gray", linestyle=":", alpha=0.5)
    plt.axhline(y=0.5, color="gray", linestyle=":", alpha=0.5)
    plt.axhline(y=0.75, color="gray", linestyle=":", alpha=0.5)

    plt.title(f"{name1} vs {name2}: {attack} Attack")
    plt.xlabel("Fraction Removed")
    plt.ylabel("Giant Component Fraction")
    plt.legend()
    plt.grid(True, alpha=0.3)

    fname = os.path.join(OUTPUT_DIR, f"COMPARE_{name1.split()[0]}_{name2.split()[0]}_{attack}.png")
    plt.savefig(fname)
    plt.close()
    print(f"Saved: {fname}")


def run_single_network_analysis(G, name, attacks):
    """
    Runs all attacks on G ONCE.
    Returns the dictionary of results to be reused later.
    """
    print(f"\n--- Analyzing {name} (Calculating Metrics) ---")
    sim = AttackSimulator(G)
    results = {}

    for atk in attacks:
        results[atk] = sim.simulate(atk)

    plot_all_strategies(name, results, 'gc', "Giant Component Size", "Robustness")
    plot_all_strategies(name, results, 'frag', "Num Components", "Fragmentation")

    return results

def run_random_baseline_analysis(G, name, real_results, attacks):
    """
    Generates a random graph, simulates it, and compares against 
    PRE-CALCULATED real_results.
    """
    print(f"\n--- Baseline {name} vs Random (Generating ER Graph) ---")

    # Generate Equivalent Random Graph
    N, E = len(G.nodes()), len(G.edges())
    # Probability for ER graph
    p = (2 * E) / (N * (N - 1)) if N > 1 else 0

    print(f"   -> Creating ER Graph (N={N}, p={p:.5f})...")
    G_rand = nx.erdos_renyi_graph(N, p, directed=G.is_directed(), seed=42)

    sim_rand = AttackSimulator(G_rand)

    for atk in attacks:
        res_real = real_results[atk]

        res_rand = sim_rand.simulate(atk)

        plot_vs_random(name, res_real, res_rand, atk)

def load_network(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return None
    print(f"Loading {path}...")
    return nx.read_edgelist(path, comments="%", nodetype=int, create_using=nx.DiGraph())

def main():
    parser = argparse.ArgumentParser(description="Network Robustness Analysis")

    parser.add_argument("-l", "--linux", action="store_true", help="Run analysis on Linux Kernel network")
    parser.add_argument("-j", "--jdk", action="store_true", help="Run analysis on JDK network")
    parser.add_argument("--all", action="store_true", help="Run analysis on BOTH networks")

    # Configuration arguments
    parser.add_argument("--attacks", nargs="+", default=["random", "degree", "indegree", "betweenness_approx"], 
                        help="List of attack strategies to simulate.")

    args = parser.parse_args()

    run_linux = args.linux or args.all
    run_jdk = args.jdk or args.all

    if not run_linux and not run_jdk:
        print("Error: You must specify a network to analyze using --linux, --jdk, or --all")
        parser.print_help()
        return

    linux_path = "data/linux/out.linux"
    java_path = "data/subelj_jdk/out.subelj_jdk_jdk"

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(">>> STARTING ANALYSIS PIPELINE <<<")

    G_lin, G_jdk = None, None
    results_lin = {}
    results_jdk = {}

    if run_linux:
        G_lin = load_network(linux_path)
        if G_lin:
            results_lin = run_single_network_analysis(G_lin, "Linux Kernel", args.attacks)

            run_random_baseline_analysis(G_lin, "Linux Kernel", results_lin, args.attacks)
        else:
            print("Skipping Linux analysis (file not found).")

    if run_jdk:
        G_jdk = load_network(java_path)
        if G_jdk:
            results_jdk = run_single_network_analysis(G_jdk, "JDK", args.attacks)

            run_random_baseline_analysis(G_jdk, "JDK", results_jdk, args.attacks)
        else:
             print("Skipping JDK analysis (file not found).")

    if run_linux and run_jdk and G_lin and G_jdk:
        print("\n--- Comparing Linux vs JDK ---")
        for atk in args.attacks:
            if atk in results_lin and atk in results_jdk:
                plot_comparison(results_lin, "Linux Kernel", results_jdk, "JDK", atk)

    elif (run_linux and run_jdk):
        print("\n! Comparison skipped: One or both networks failed to load.")

    print("\n>>> PIPELINE COMPLETE. <<<")

if __name__ == "__main__":
    main()
