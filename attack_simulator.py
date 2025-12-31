import networkx as nx
import matplotlib.pyplot as plt
import random
import argparse
import os



OUTPUT_DIR = "graphs"

# ==========================================
# 1. SIMULATION ENGINE
# ==========================================

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
        
        # Use generator to save memory
        if G.is_directed():
            components = nx.weakly_connected_components(G)
        else:
            components = nx.connected_components(G)
            
        try:
            # fast max find without instantiating subgraph
            return max(len(c) for c in components)
        except ValueError:
            return 0

    def simulate(self, strategy="random", steps=50):
        print(f"   -> Simulating strategy: {strategy}...")
        G = self.graph.copy()
        N = len(G)

        # --- OPTIMIZATION: Strategy Selection ---
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

        # --- Execution ---
        chunk = max(1, int(N / steps))
        # Note: 'diam' removed from tracking for speed
        res = {'x': [0.0], 'gc': [1.0], 'frag': []} 

        # Initial Metrics
        res['frag'].append(
            nx.number_weakly_connected_components(G) if G.is_directed() 
            else nx.number_connected_components(G)
        )

        removed_count = 0
        
        for _ in range(steps):
            if removed_count >= N: break
            
            # Remove batch
            batch = nodes[removed_count : removed_count + chunk]
            G.remove_nodes_from(batch)
            removed_count += len(batch)

            # --- OPTIMIZATION: Fast Metric Calculation ---
            # 1. GC Size (No copying)
            gc_sz = self.get_gc_size_only(G)
            
            # 2. Fragmentation (Fast O(N+E))
            frag = (nx.number_weakly_connected_components(G) 
                    if G.is_directed() 
                    else nx.number_connected_components(G))

            # 3. Diameter (SKIPPED FOR SPEED)
            # If you REALLY need this, use: nx.approximation.diameter(G)
            # But even that will slow you down significantly.
            
            res['x'].append(removed_count / self.initial_size)
            res['gc'].append(gc_sz / self.initial_gc_size)
            res['frag'].append(frag)

            if gc_sz == 0: break
            
        return res


# ==========================================
# 2. PLOTTING HELPERS
# ==========================================

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
        plt.axhline(y=0.5, color="red", linestyle=":", label="50% Threshold")

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
    
    plt.axhline(y=0.5, color="gray", linestyle=":", alpha=0.5)
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
    
    plt.axhline(y=0.5, color="gray", linestyle=":", alpha=0.5)
    plt.title(f"{name1} vs {name2}: {attack} Attack")
    plt.xlabel("Fraction Removed")
    plt.ylabel("Giant Component Fraction")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    fname = os.path.join(OUTPUT_DIR, f"COMPARE_{name1.split()[0]}_{name2.split()[0]}_{attack}.png")
    plt.savefig(fname)
    plt.close()
    print(f"Saved: {fname}")

# ==========================================
# 3. ANALYSIS CONTROLLERS (OPTIMIZED)
# ==========================================

def run_single_network_analysis(G, name, attacks):
    """
    Runs all attacks on G ONCE.
    Returns the dictionary of results to be reused later.
    """
    print(f"\n--- Analyzing {name} (Calculating Metrics) ---")
    sim = AttackSimulator(G)
    results = {}
    
    for atk in attacks:
        # This is the ONLY time we simulate the real network
        results[atk] = sim.simulate(atk)
        
    # Plot All Strategies on One Graph
    # (Removed Diameter plot as discussed)
    plot_all_strategies(name, results, 'gc', "Giant Component Size", "Robustness")
    plot_all_strategies(name, results, 'frag', "Num Components", "Fragmentation")
    
    return results

def run_random_baseline_analysis(G, name, real_results, attacks):
    """
    Generates a random graph, simulates it, and compares against 
    PRE-CALCULATED real_results.
    """
    print(f"\n--- Baseline {name} vs Random (Generating ER Graph) ---")
    
    # 1. Generate Equivalent Random Graph
    N, E = len(G.nodes()), len(G.edges())
    # Probability for ER graph
    p = (2 * E) / (N * (N - 1)) if N > 1 else 0
    
    print(f"   -> Creating ER Graph (N={N}, p={p:.5f})...")
    G_rand = nx.erdos_renyi_graph(N, p, directed=G.is_directed(), seed=42)
    
    # 2. Simulate ONLY the Random Graph
    sim_rand = AttackSimulator(G_rand)
    
    for atk in attacks:
        # RETRIEVE existing real results (Instant)
        res_real = real_results[atk]
        
        # CALCULATE new random results
        res_rand = sim_rand.simulate(atk)
        
        # Plot Comparison
        plot_vs_random(name, res_real, res_rand, atk)


# ==========================================
# 4. MAIN & SETUP (OPTIMIZED FLOW)
# ==========================================

def load_network(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return None
    print(f"Loading {path}...")
    return nx.read_edgelist(path, comments="%", nodetype=int, create_using=nx.DiGraph())

def main():
    parser = argparse.ArgumentParser(description="Network Robustness Analysis")
    
    # Selection arguments
    parser.add_argument("-l", "--linux", action="store_true", help="Run analysis on Linux Kernel network")
    parser.add_argument("-j", "--jdk", action="store_true", help="Run analysis on JDK network")
    parser.add_argument("--all", action="store_true", help="Run analysis on BOTH networks")
    
    # Configuration arguments
    parser.add_argument("--attacks", nargs="+", default=["random", "degree", "indegree", "betweenness_approx"], 
                        help="List of attack strategies to simulate.")
    
    args = parser.parse_args()

    # Determine what to run
    run_linux = args.linux or args.all
    run_jdk = args.jdk or args.all

    # If user didn't select anything, print help and exit
    if not run_linux and not run_jdk:
        print("Error: You must specify a network to analyze using --linux, --jdk, or --all")
        parser.print_help()
        return

    # PATHS (Update these!)
    linux_path = "data/linux/out.linux"
    java_path = "data/subelj_jdk/out.subelj_jdk_jdk"
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(">>> STARTING OPTIMIZED ANALYSIS PIPELINE <<<")
    
    # Initialize containers
    G_lin, G_jdk = None, None
    results_lin = {}
    results_jdk = {}

    # -----------------------------
    # 1. Linux Analysis
    # -----------------------------
    if run_linux:
        G_lin = load_network(linux_path)
        if G_lin:
            # A. Run Simulation ONCE
            results_lin = run_single_network_analysis(G_lin, "Linux Kernel", args.attacks)
            
            # B. Compare against Random (Passing existing results)
            run_random_baseline_analysis(G_lin, "Linux Kernel", results_lin, args.attacks)
        else:
            print("Skipping Linux analysis (file not found).")

    # -----------------------------
    # 2. JDK Analysis
    # -----------------------------
    if run_jdk:
        G_jdk = load_network(java_path)
        if G_jdk:
            # A. Run Simulation ONCE
            results_jdk = run_single_network_analysis(G_jdk, "JDK", args.attacks)
            
            # B. Compare against Random (Passing existing results)
            run_random_baseline_analysis(G_jdk, "JDK", results_jdk, args.attacks)
        else:
             print("Skipping JDK analysis (file not found).")

    # -----------------------------
    # 3. Cross-Network Comparison
    # -----------------------------
    # Only run this if BOTH were requested AND BOTH loaded successfully
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
