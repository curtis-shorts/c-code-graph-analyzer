import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import matplotlib.cm as cm
import random
from copy import deepcopy
import matplotlib.colors as mcolors

class GraphVisualization:
    def __init__(self):
        self.edges_list = []
        self.inbound_dependencies = {}

    def addEdge(self, a, b, c):
        self.edges_list.append([a, b, c])
        # Track dependencies
        if b not in self.inbound_dependencies:
            self.inbound_dependencies[b] = 0
        self.inbound_dependencies[b] += c

    def generate_random_partition(self, nodes, k):
        random.shuffle(nodes)
        return [nodes[i::k] for i in range(k)]

    def modular_quality(self, partition, graph, run_weighted_flag):
        # Compute the modular quality (MQ) of a partition, bounded between -1 and 1
        # MQ aims to maximize intraconnectivity and minimize interconnectivity

        # Changes to MQ in order to add weighting
        if run_weighted_flag:
            total_weight = sum(data['weight'] for _, _, data in graph.edges(data=True))
            if total_weight == 0:
                return 0

        # The connectivity within a cluster, bounded between 0 and 1
        # intra-edges / max intra-edge dependencies possible (modules^2)
        def intraconnectivity(cluster):
            intra_edges = 0
            intra_modules = len(cluster)
            for node in cluster:
                for neighbor in graph.neighbors(node):
                    if neighbor in cluster:
                        intra_edges += 1
            if intra_modules == 0:
                return 1
            return intra_edges / intra_modules**2
        
        def weighted_intraconnectivity(cluster):
            intra_weight = 0
            intra_modules = len(cluster)
            for node in cluster:
                for neighbor in graph.neighbors(node):
                    if neighbor in cluster:
                        intra_weight += graph[node][neighbor]['weight']
            if intra_modules == 0:
                return 1
            return intra_weight / (total_weight * intra_modules)

        # The connectivity between two clusters, bounded between 0 and 1
        # inter-edges / (2 * edges in i * edges in j)
        def interconnectivity(cluster_i, cluster_j):
            inter_edges = 0
            nodes_i = len(cluster_i)
            nodes_j = len(cluster_j)
            if cluster_i != cluster_j:
                # Edges from i to j
                for node in cluster_i:
                    for neighbor in graph.neighbors(node):
                        if neighbor in cluster_j:
                            inter_edges += 1
                # Edges from j to i
                for node in cluster_j:
                    for neighbor in graph.neighbors(node):
                        if neighbor in cluster_i:
                            inter_edges += 1
                if nodes_i == 0:
                    return 1
                elif nodes_j == 0:
                    return 1
                return inter_edges / (2 * nodes_i * nodes_j)
            else:
                return 0
        
        def weighted_interconnectivity(cluster_i, cluster_j):
            inter_weight = 0
            nodes_i = len(cluster_i)
            nodes_j = len(cluster_j)
            if cluster_i != cluster_j:
                for node in cluster_i:
                    for neighbor in graph.neighbors(node):
                        if neighbor in cluster_j:
                            inter_weight += graph[node][neighbor]['weight']
                if nodes_i == 0 or nodes_j == 0:
                    return 1
                return inter_weight / (2 * nodes_i * nodes_j)
            else:
                return 0

        # mq = 1/k * (sum of inter - cluster const * (sum of intra))
        mq = 0
        cluster_count = len(partition)
        if cluster_count == 1:
            return 1
        if cluster_count == 0:
            return 0
        partition_constant = 1 / (cluster_count * (cluster_count - 1)) / 2
        for cluster_i in partition:
            if run_weighted_flag:
                A_i = weighted_intraconnectivity(cluster_i)
            else:
                A_i = intraconnectivity(cluster_i)
            E_i_j = 0
            for cluster_j in partition:
                if run_weighted_flag:
                    E_i_j += weighted_interconnectivity(cluster_i, cluster_j)
                else:
                    E_i_j += interconnectivity(cluster_i, cluster_j)
            mq += A_i - (partition_constant * E_i_j)
        mq = (1 / cluster_count) * mq
        return mq

    def find_better_partition(self, current_partition, graph, run_weighted_flag):
        # Find a better neighboring partition by moving a node to a different cluster.
        best_partition = current_partition
        best_mq = self.modular_quality(current_partition, graph, run_weighted_flag)

        for i, cluster in enumerate(current_partition):
            for node in cluster:
                # Attempt to move node to every other cluster
                for j, target_cluster in enumerate(current_partition):
                    if i != j:
                        new_partition = deepcopy(current_partition)
                        new_partition[i].remove(node)
                        new_partition[j].append(node)
                        new_mq = self.modular_quality(new_partition, graph, run_weighted_flag)
                        if new_mq > best_mq:
                            best_partition = new_partition
                            best_mq = new_mq
        return best_partition if best_partition != current_partition else None

    def sub_optimal_clustering(self, graph, k, run_weighted_flag):
        # Initialize the clustering state
        nodes = list(graph.nodes)
        partition = self.generate_random_partition(nodes, k)

        while True:
            better_partition = self.find_better_partition(partition, graph, run_weighted_flag)
            if better_partition:
                partition = better_partition
            else:
                break
        return [self.modular_quality(partition, graph, run_weighted_flag), partition]

    def genetic_clustering(self, graph, k, run_weighted_flag, population_size=10, max_generations=100):
        # Initialize the clustering state
        nodes = list(graph.nodes)
        population = [self.generate_random_partition(nodes, k) for _ in range(population_size)]

        for generation in range(max_generations):
            # Improve a percentage of partitions
            for partition in population[: population_size // 2]:
                better_partition = self.find_better_partition(partition, graph, run_weighted_flag)
                if better_partition:
                    population[population.index(partition)] = better_partition

            # Generate a new population biased by MQ scores
            scores = [self.modular_quality(partition, graph, run_weighted_flag) for partition in population]
            total_score = sum(scores)
            if total_score != 0:
                probabilities = [score / total_score for score in scores]
            else:
                probabilities = [score / 1 for score in scores]
            # Handle cases where all scores are zero
            #else:
            #    probabilities = [1 / len(scores)] * len(scores)
            
            new_population = random.choices(population, probabilities, k=population_size)

            if new_population == population:  # Check for convergence
                break
            population = new_population

        # Return the best partition found
        best_partition = max(population, key=lambda p: self.modular_quality(p, graph, run_weighted_flag))
        return [self.modular_quality(best_partition, graph, run_weighted_flag), best_partition]

    def find_isolated_branches(self, graph):
        connected_components = nx.connected_components(graph)
        return [list(component) for component in connected_components]

    def visualize(self, clustering_method, k, graph_file_name, random_samples, gen_plot, color_by_dependencies):
        # K is the number of clusters that will be generated
        # Initialize the graph
        my_graph = nx.Graph()
        my_graph.add_edges_from([[a, b, {'weight': c}] for a,b,c in self.edges_list])
        dynamic_k = 0
        if k == 0:
            dynamic_k = 1

        # First find any isolated clusters
        isolated_clusters = self.find_isolated_branches(my_graph)
        if not isolated_clusters:
            isolated_clusters = [my_graph.nodes()]

        # Process each isolated cluster separately
        all_clusters = []
        mq_values = []
        for i, isolated_nodes in enumerate(isolated_clusters, start=1):
            subgraph = my_graph.subgraph(isolated_nodes)

            # Set a dynamic k value
            if dynamic_k:
                node_count = len(isolated_nodes)
                if node_count < 5:
                    k = 1
                elif node_count < 7:
                    k = 2
                elif node_count < 15:
                    k = 3
                elif node_count < 25:
                    k = 4
                else:
                    k = 5

            if len(isolated_nodes) < max(k + 1, 5):
                run_weighted_flag = 0
                mq_value, clusters = self.sub_optimal_clustering(subgraph, 1, run_weighted_flag)
                i += 1
            else:
                best_clusters = None
                best_mq = -1
                for _ in range(random_samples):
                    if clustering_method == "suboptimal" or not color_by_dependencies:
                        run_weighted_flag = 0
                        mq_value, clusters = self.sub_optimal_clustering(subgraph, k, run_weighted_flag)
                    elif clustering_method == "genetic":
                        run_weighted_flag = 0
                        mq_value, clusters = self.genetic_clustering(subgraph, k, run_weighted_flag)
                    elif clustering_method == "suboptimal_weighted":
                        run_weighted_flag = 1
                        mq_value, clusters = self.sub_optimal_clustering(subgraph, k, run_weighted_flag)
                    elif clustering_method == "genetic_weighted":
                        run_weighted_flag = 1
                        mq_value, clusters = self.genetic_clustering(subgraph, k, run_weighted_flag)
                    else:
                        raise ValueError("Unknown clustering method.")
                    if mq_value > best_mq:
                        best_clusters = clusters
                        best_mq = mq_value
                mq_value = best_mq
                clusters = best_clusters
            
            # Append the clusters found in the subgraph to the overall list
            all_clusters.extend(clusters)
            mq_values.append(mq_value)
        
        mq_mean = sum(mq_values) / len(isolated_clusters)

        # Remove empty clusters from the partition
        all_clusters = [file_list for file_list in all_clusters if file_list]
        # Create a dictionary to map cluster IDs to a list of nodes
        clusters_colored = {}
        for cluster_id, cluster in enumerate(all_clusters):
            clusters_colored[cluster_id] = []
            for node in cluster:
                clusters_colored[cluster_id].append(node)

        # To plot or not to plot, that is the question
        if not gen_plot:
            return [mq_mean, clusters_colored]

        # Position the nodes in a circular layout
        pos = nx.circular_layout(my_graph)

        if color_by_dependencies:
            plt.figure(figsize=(12, 8))
        else:
            plt.figure(figsize=(10, 8))

        # Extract edge weights and normalize to control the thickness range
        weights = [my_graph[u][v]['weight'] for u, v in my_graph.edges()]

        scaling_factor = 3
        normalizer = max(weights) + 1
        normalized_weights = [scaling_factor * (weight + 1) / normalizer for weight in weights]

        # Draw edges with thickness proportional to their weights
        nx.draw_networkx_edges(my_graph, pos, width=normalized_weights)

        # Prepare node coloring
        if color_by_dependencies:
            # Count inbound dependencies for each node and normalize the colors
            dependency_counts = self.inbound_dependencies
            max_dependencies = max(max(dependency_counts.values()), 1) if dependency_counts else 1
            node_colors = [dependency_counts.get(node, 0) / max_dependencies for node in my_graph.nodes()]
            
            # Draw nodes with dependency-based colors
            cmap = cm.YlOrRd
            nx.draw_networkx_nodes(my_graph, pos, node_color=node_colors, cmap=cmap,
                                    edgecolors='black', node_size=400)
            # Add a colorbar
            if max_dependencies > 800:
                ax = plt.gca()
                norm = mcolors.LogNorm(vmin=1, vmax=max_dependencies + 1)
                sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
                sm.set_array([])
            else:
                ax = plt.gca()
                norm = plt.Normalize(vmin=0, vmax=max_dependencies)
                sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
                sm.set_array([])
            plt.colorbar(sm, ax=ax, label='Inbound Dependencies')
        else:
            # Cluster-based coloring
            unique_clusters = set(clusters_colored.keys())
            for cluster_id in unique_clusters:
                cluster_nodes = clusters_colored[cluster_id]
                nx.draw_networkx_nodes(my_graph, pos, nodelist=cluster_nodes,
                        node_color=f"C{cluster_id}", edgecolors='black',
                        label=f'Cluster {cluster_id + 1}',
                        node_size=400)
        
        labels = nx.draw_networkx_labels(my_graph, pos, font_weight='bold', font_color='black', font_size=14)
        # Add a black outline to each label
        for label in labels.values():
            label.set_path_effects([
                path_effects.Stroke(linewidth=2, foreground='white'),
                path_effects.Normal()
            ])
        
        # Dynamically change the plot margins depending on the label lengths
        labels = {node: str(node) for node in my_graph.nodes()}
        longest_label = len(max(labels.values()))
        if not color_by_dependencies:
            offset = 0.1
        if longest_label > 10:
            plt.margins(0.1)
        if longest_label > 20:
            plt.margins(0.16)
        if longest_label > 25:
            plt.margins(0.2)

        # Save and close the plot
        if not color_by_dependencies:
            plt.legend(scatterpoints=1, loc="upper left", fontsize=18)
        plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
        plt.savefig(graph_file_name, dpi=800)
        plt.close()

        return [mq_mean, clusters_colored]

