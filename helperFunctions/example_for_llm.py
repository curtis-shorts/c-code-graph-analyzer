import networkx as nx
import random

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

    # Supporting functions for clustering algorithms

    def sub_optimal_clustering(self, graph, k=3):
        # Initialize the clustering state
        nodes = list(graph.nodes)
        partition = self.generate_random_partition(nodes, k)

        while True:
            better_partition = self.find_better_partition(partition, graph)
            if better_partition:
                partition = better_partition
            else:
                break
        return [self.modular_quality(partition, graph), partition]

    def genetic_clustering(self, graph, k=3, population_size=10, max_generations=100):
        # Initialize the clustering state
        nodes = list(graph.nodes)
        population = [self.generate_random_partition(nodes, k) for _ in range(population_size)]

        for generation in range(max_generations):
            # Improve a percentage of partitions
            for partition in population[: population_size // 2]:
                better_partition = self.find_better_partition(partition, graph)
                if better_partition:
                    population[population.index(partition)] = better_partition

            # Generate a new population biased by MQ scores
            scores = [self.modular_quality(partition, graph) for partition in population]
            total_score = sum(scores)
            if total_score != 0:
                probabilities = [score / total_score for score in scores]
            else:
                probabilities = [score / 1 for score in scores]
            new_population = random.choices(population, probabilities, k=population_size)

            if new_population == population:  # Check for convergence
                break
            population = new_population

        # Return the best partition found
        best_partition = max(population, key=lambda p: self.modular_quality(p, graph))
        return [self.modular_quality(best_partition, graph), best_partition]

    def find_isolated_branches(self, graph):
        connected_components = nx.connected_components(graph)
        return [list(component) for component in connected_components]

    def visualize(self, clustering_method, k, random_samples):
        # K is the number of clusters that will be generated
        # Initialize the graph
        my_graph = nx.Graph()
        my_graph.add_edges_from([[a, b, {'weight': c}] for a,b,c in self.edges_list])

        # First find any isolated clusters
        isolated_clusters = self.find_isolated_branches(my_graph)
        if not isolated_clusters:
            isolated_clusters = [my_graph.nodes()]

        # Process each isolated cluster separately
        all_clusters = []
        mq_values = []
        for i, isolated_nodes in enumerate(isolated_clusters, start=1):
            subgraph = my_graph.subgraph(isolated_nodes)

            if len(isolated_nodes) < max(k + 1, 5):
                mq_value, clusters = self.sub_optimal_clustering(subgraph, 1)
                i += 1
            else:
                best_clusters = None
                best_mq = -1
                for _ in range(random_samples):
                    if clustering_method == "suboptimal":
                        mq_value, clusters = self.sub_optimal_clustering(subgraph, k)
                    elif clustering_method == "genetic":
                        mq_value, clusters = self.genetic_clustering(subgraph, k)
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

        return [mq_mean, clusters_colored]
    




# Unique weighted MQ from GPT
def modular_quality(self, partition, graph):
    """Compute a modularity-like score that accounts for edge weights."""
    total_weight = sum(data['weight'] for _, _, data in graph.edges(data=True))
    if total_weight == 0:
        return 0

    intra_cluster_weight = 0
    for cluster in partition:
        for i, node1 in enumerate(cluster):
            for node2 in cluster[i + 1:]:
                if graph.has_edge(node1, node2):
                    intra_cluster_weight += graph[node1][node2]['weight']

    return intra_cluster_weight / total_weight

# Imporved weighted MQ derived from original
def modular_quality(self, partition, graph):
    """Compute the modular quality (MQ) of a partition, accounting for edge weights."""
    total_weight = sum(data['weight'] for _, _, data in graph.edges(data=True))
    if total_weight == 0:
        return 0

    #def intraconnectivity()

    # Connectivity between two clusters
    def interconnectivity(cluster_i, cluster_j):
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

    mq = 0
    cluster_count = len(partition)
    if cluster_count == 1:
        return 1
    partition_constant = 1 / (cluster_count * (cluster_count - 1)) / 2
    for cluster_i in partition:
        A_i = intraconnectivity(cluster_i)
        E_i_j = 0
        for cluster_j in partition:
            E_i_j += interconnectivity(cluster_i, cluster_j)
        mq += A_i - (partition_constant * E_i_j)
    mq = (1 / cluster_count) * mq
    return mq




