import os
import re
from helperFunctions.graphVisualization import GraphVisualization
import helperFunctions.nodesStructs as nodesStructs
from contextlib import redirect_stdout

def getLeafFilesHelper(obj, resolved_files):
    # If the object is a ClusterNode, recursively process its files
    if type(obj) == nodesStructs.ClusterNode:
        for file in obj.files_list.values():
            getLeafFilesHelper(file, resolved_files)
    else:
        # Add the file to the resolved list
        resolved_files.append(obj)
    return

def runGraphGeneration(objects_list, algorithm, k, graph_name, random_samples,
                       gen_plot, base_dir_extension, color_by_dependencies_flag):
    gv = GraphVisualization()

    filtered_objects = [obj for obj in objects_list if obj.name.startswith(base_dir_extension)
                                and obj.name != base_dir_extension + ":0"]

    # Flatten the objects list to only contain files
    files_list = []
    for obj in filtered_objects:
        getLeafFilesHelper(obj, files_list)

    def addEdgeHelper(graph, file, top_level_parent, objects_list, files_list):
        # Resolve the from node name
        if top_level_parent == None:
            from_node = file.name
        else:
            from_node = top_level_parent.name
        
        # Draw edges for each dependency of the file/cluster
        for dependancy in file.file_dependencies.keys():
            # Check the edge isn't a loopback
            if file.name == dependancy:
                continue
            # Check that the dependency is part of the partition
            if dependancy not in [f.name for f in files_list]:
                continue

            # Resolve the to node name (check if it has a parent cluster)
            def findNodeInClusterHelper(objects_list, dependency, max_depth=3):
                def recursive_search(items, current_depth):
                    # If we've reached max depth, stop searching
                    if current_depth >= max_depth:
                        return None
                    for item in items:
                        # If item is a ClusterNode
                        if type(item) == nodesStructs.ClusterNode:
                            # Check if dependency is in this ClusterNode's files_list
                            if dependency in item.files_list.keys():
                                return item.name
                            nested_items = list(item.files_list.values())
                            nested_result = recursive_search(
                                [obj for obj in nested_items if type(obj) == nodesStructs.ClusterNode],
                                current_depth + 1
                            )
                            if nested_result:
                                return item.name
                    return None
                return recursive_search(objects_list, 0) or dependency

            to_node = findNodeInClusterHelper(objects_list, dependancy, max_depth=6)

            # Check that the to/from nodes aren't the same (can happen if files are in the same cluster)
            if from_node == to_node:
                continue
            if not from_node.startswith(base_dir_extension) or not to_node.startswith(base_dir_extension):
                print("ERROR: something wrong with base_dir handling")
            # Get the edge weight
            edge_weight = file.file_dependencies[dependancy]
            # Check if the reverse edge already exists and sum the weights if so
            reverse_edge = [to_node, from_node]
            for i, (a,b,c) in enumerate(graph.edges_list):
                if [a,b] == reverse_edge:
                    graph.edges_list[i] = (a, b, c + edge_weight)
                    graph.inbound_dependencies[b] += edge_weight
                    break
            else:
                graph.addEdge(from_node, to_node, edge_weight)

    def resolveDependenciesHelper(graph, obj, top_level_parent, objects_list, files_list):
        # Cluster case (possibly recursive)
        if type(obj) == nodesStructs.ClusterNode:
            # Iterate over the files in the cluster
            for next_obj in obj.getFileDependencies():
                if type(next_obj) == nodesStructs.ClusterNode:
                    # Recursively handle nested ClusterNodes
                    resolveDependenciesHelper(graph, next_obj, top_level_parent, objects_list, files_list)
                else:
                    # Handle regular files with a parent ClusterNode
                    addEdgeHelper(gv, next_obj, top_level_parent, objects_list, files_list)
        # File without parent cluster case
        else:
            addEdgeHelper(gv, obj, None, objects_list, files_list)

    # Check which files depend on one another and re-assemble the cluster dependencies bottom-up
    for obj in filtered_objects:
        resolveDependenciesHelper(gv, obj, obj, filtered_objects, files_list)
    
    # Run the clustering algorithm
    mean_mq = 1
    clusters = {}
    if gv.edges_list:
        mean_mq, clusters = gv.visualize(algorithm, k, graph_name, random_samples, gen_plot,
                                         color_by_dependencies_flag)
    
    # Flatten the list of edges to find objects that didn't make it in the graph
    connected_nodes = [node for edge in gv.edges_list for node in edge]
    connected_nodes = list(set(connected_nodes))
    unconnected_files = [o.name for o in filtered_objects if o.name not in connected_nodes]
    # Assign unconnected files to their own clusters
    next_cluster_id = max(clusters.keys(), default=-1)
    for file_name in unconnected_files:
        next_cluster_id += 1
        clusters[next_cluster_id] = [file_name]

    # Return the results
    return mean_mq, clusters

def executeClusterWorkflow(files_dict, algorithm, source_dir, output_dir, k_values,
                           random_samples, directories_of_interest, project_name, max_plot_depth):
    # Recursive function to traverse into the directory tree
    def clusterRecursionHelper(files_list, base_dir, current_depth, plot_depth,
                                clusters_dict, graph_dir, k_target, k_other):
        iterative_removal = []

        # Filter the files list to only include files in the relevant subdirectories
        new_files_list = [f for f in files_list if base_dir in f.name]
        
        # Setup data for the specific execution depth
        if base_dir == '':
            base_dir_resolved = project_name
            run_dir_path = source_dir
            new_graph_dir = graph_dir
        else:
            base_dir_resolved = base_dir
            run_dir_path = os.path.join(source_dir, base_dir)
            # Set the graph directory unless we're at the deepest level
            if current_depth < plot_depth:
                new_graph_dir = graph_dir + re.sub(r'.+/', '/', base_dir)
                # Make the graph directory if it doesn't exist
                os.makedirs(new_graph_dir, exist_ok=True)
            else:
                new_graph_dir = graph_dir

        # Recursively go into the subdirectories
        subdirs = [f.path for f in os.scandir(run_dir_path) if f.is_dir()]
        if subdirs:
            for dir in subdirs:
                dir = dir.replace(source_dir, '')
                # Only want to look at directories of interest at the top level
                if not dir.startswith(directories_of_interest):
                    continue
                removal_list = clusterRecursionHelper(new_files_list, dir, current_depth + 1,
                                    plot_depth, clusters_dict, new_graph_dir, k_target, k_other)
                iterative_removal.extend(removal_list)
            new_files_list = [f for f in new_files_list if f not in iterative_removal]

        # Name the graph for this level
        graph_name = graph_dir + '/' + base_dir_resolved.replace('/', '_')
        
        # Check if the graph needs to be generated
        generate_plot = 1
        if current_depth > plot_depth:
            generate_plot = 0

        # Plot depth testing
        if current_depth == plot_depth:
            generate_plot = 1
            k_resolved = k_target
        else:
            generate_plot = 0
            k_resolved = k_other
        
        # Colors by dependencies into/out of a file instead of by cluster
        color_by_dependencies_flag = 0
        if k_resolved == -1:
            color_by_dependencies_flag = 1
        
        # Cluster the files
        mean_mq, clusters = runGraphGeneration(new_files_list, algorithm, k_resolved, graph_name,
                                random_samples, generate_plot, base_dir, color_by_dependencies_flag)

        # Build ClusterNodes for the current level
        cluster_nodes = {}
        for cluster_id, cluster_files in clusters.items():
            cluster_file_objects = []
            for name in cluster_files:
                for obj in new_files_list:
                    if obj.name == name:
                        cluster_file_objects.append(obj)
                        break
            cluster_node = nodesStructs.ClusterNode(source_dir, base_dir, cluster_id, cluster_file_objects)
            cluster_node.mean_mq = mean_mq
            cluster_nodes[cluster_node.name] = cluster_node
            
            # Add the cluster to the list so it's passed back in recursion return
            files_list.append(cluster_node)
            for file_name in cluster_node.files_list:
                for file_obj in files_list:
                    if file_name == file_obj.name:
                        iterative_removal.append(file_obj)

        # Add the ClusterNode to the dict
        clusters_dict[base_dir_resolved] = {
            "mq_value": mean_mq,
            "cluster_nodes": cluster_nodes
        }

        #print(clusters_dict)
        #print([c['mq_value'] for c in clusters_dict.values()])
        #exit()

        return iterative_removal

    # Aggregate MQ values and metrics
    if k_values[0] == -1:
        graph_dir = f"{output_dir}/graphs_heatmap/"
    else:
        graph_dir = f"{output_dir}/graphs_{algorithm}/"
    os.makedirs(graph_dir, exist_ok=True)

    # Flatten the files
    files_list = [file for run_dir in files_dict.keys() for file in files_dict[run_dir].values()]
    
    clusters_dict = {}
    clusterRecursionHelper(files_list, '', 0, 3, clusters_dict, graph_dir, k_values[0], k_values[0])
    #print([d for c in clusters_dict for d in c.values()])
    mq_list = [c['mq_value'] for c in clusters_dict.values()]
    one_mq_list = [c['mq_value'] for c in clusters_dict.values() if c['mq_value'] != 1]
    print(len(mq_list), len(mq_list) - len(one_mq_list), sum(one_mq_list)/len(one_mq_list))
    #exit()


    # Recursively execute at each depth
    #for depth in range(max_plot_depth):
    #    clusters_dict = {}
    #    clusterRecursionHelper(files_list, '', 0, depth, clusters_dict, graph_dir, k_values[0], 1)

    # Print the extracted data
    csv_file = f'{graph_dir}/test_file_depth_all.csv'
    #csv_file = f'{graph_dir}/test_file_depth_{depth}.csv'
    with open(csv_file, 'w') as f:
        with redirect_stdout(f):
            print('file_path,mq_value,total_files,lines_of_code,total_functions,total_macros,cluster_children')
            
            for dict_key in clusters_dict:
                mq_value = clusters_dict[dict_key]['mq_value']
                sub_clusters_dict = clusters_dict[dict_key]['cluster_nodes']
                lines_of_code = 0
                for cluster_instance, cluster_obj in sub_clusters_dict.items():
                    if cluster_instance.startswith(':'):
                        cluster_instance = project_name + cluster_instance
                    cluster_children = [f.name for f in cluster_obj.getFileDependencies()]
                    leaf_file_objects = []
                    getLeafFilesHelper(cluster_obj, leaf_file_objects)
                    lines_of_code = sum([f.lines_in_file for f in leaf_file_objects])
                    total_files = len(leaf_file_objects)
                    total_functions = sum([len(f.other_definitions) for f in leaf_file_objects])
                    total_macros = sum([len(f.macro_definitions) for f in leaf_file_objects])
                    cluster_children_string = '; '.join(map(str,cluster_children))
                    print(f"{cluster_instance},{mq_value},{total_files},{lines_of_code},{total_functions},{total_macros},{cluster_children_string}")
