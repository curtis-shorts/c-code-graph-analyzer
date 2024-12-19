import os
import pickle
from helperFunctions.handleFileDependencies import getFileDependencies
from helperFunctions.handleFileDependencies import reconstrainFileReferences
from helperFunctions.clusterWorkflow import executeClusterWorkflow
from helperFunctions.joinCAndHFiles import joinCAndHFiles
import argparse
from contextlib import redirect_stdout

# Goals for this work:
#       Implement a weighted graph clustering algorithm (e.g. networkx's louvain_partitions)
#       Get a good overview of UCS/UCT/UCP, analyse what clustering method is best
#       See if it's possible to cluster each of UCS/UCT/UTP all at once
#       Isolate for macro/function dependencies and see how they are different
#       Analyse which unweighted clustering algorithm leads to better MQ values

############### INPUT VARIABLES ###############
parser = argparse.ArgumentParser()
parser.add_argument("-s", "--source_dir", help = "Path to the source code directory.", required=True)
parser.add_argument("-o", "--outputs_dir", help = "Path to the directory to use for output files.", required=True)
parser.add_argument("-p", "--project", help = "The name of the project being analysed.", required=True)
parser.add_argument("-d", "--directories", help = "The list of sub-directories to observe in SOURCE_DIR.", nargs='+', required=True)
parser.add_argument("-a", "--algorithm", help = "The algorithm to use: 0 - Suboptimal, 1 - Genetic, 2 - Suboptimal (Weighted), 3 - Genetic (Weighted)", required=True, type=int)
parser.add_argument("--random_samples", help = "The number of random start points to cycle through for the algorithm.", default=1, type=int)
parser.add_argument("--heatmap", help = "Flag to print heatmaps instead of clusters.", default=0, type=int)
parser.add_argument("--macros_only", help = "Flag to only consider macro dependencies, not functions.", default=0, type=int)
parser.add_argument("--functions_only", help = "Flag to only consider function dependencies, not macros.", default=0, type=int)
parser.add_argument("--joint_files", help = "Flag to join files of the same name (.c, .h, and .c4).", default=1, type=int)
parser.add_argument("--max_plot_depth", help = "The number of directories to plot recursively (top level is 0).", default=3, type=int)
args = parser.parse_args()

if args.macros_only and args.functions_only:
    print("ERROR: only one flag out of macros_only and functions_only can be set at once!")
    exit(1)

if __name__ == "__main__":
    ############### INITIALIZATION ###############
    # File path info
    output_dir = f'{args.outputs_dir}/{args.project}_outputs'
    pickle_name = f'{args.project}_files_data.pkl'
    antlr_err_name = f'{args.project}_antlr_error_outputs.txt'
    pickle_path = f'{output_dir}/{pickle_name}'
    antlr_err_outputs = f'{output_dir}/antlr_error_outputs.txt'
    os.makedirs(output_dir, exist_ok=True)
    # Handle file extensions for different dependency considerations
    if args.macros_only:
        output_dir += "/macros_only"
        os.makedirs(output_dir, exist_ok=True)
    elif args.functions_only:
        output_dir += "/functions_only"
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir += "/all_dependencies"
        os.makedirs(output_dir, exist_ok=True)
    # Other runtime variables
    generate_files = 0
    if not os.path.exists(pickle_path):
        generate_files = 1
    algorithm = ("suboptimal", "genetic", "suboptimal_weighted", "genetic_weighted")[args.algorithm]
    # -1 is heatmap, 0 is dynamic, other is the specific # of clusters
    if args.heatmap:
        k_values = (-1,-1,-1)
    else:
        k_values = (0, 0, 0)

    ############### DATA COLLECTION ###############
    # Get the dependancy data for all the files in the project
    if generate_files:
        files_dict = getFileDependencies(args.source_dir, args.directories, antlr_err_outputs)
        # Save files_dict to a file
        with open(pickle_path, "wb") as f:
            pickle.dump(files_dict, f)
    else:
        with open(pickle_path, "rb") as f:
            files_dict = pickle.load(f)
    
    # Combine the .c and .h files for better utility
    if args.macros_only:
        reconstrainFileReferences(args.directories, files_dict, 'macros')
    elif args.functions_only:
        reconstrainFileReferences(args.directories, files_dict, 'functions')
    elif 1: #args.joint_files:
        files_dict = joinCAndHFiles(files_dict, args.source_dir)
    
    # Get metadata for the whole codebase
    csv_file = f'{output_dir}/test_file_full.csv'
    files_list = [file for run_dir in files_dict.keys() for file in files_dict[run_dir].values()]
    with open(csv_file, 'w') as f:
        with redirect_stdout(f):
            total_files = len(files_list)
            lines_of_code = sum([f.lines_in_file for f in files_list])
            c_files = len([f.name for f in files_list if f.name.endswith('.c')])
            h_files = len([f.name for f in files_list if f.name.endswith('.h')])
            inl_files = len([f.name for f in files_list if f.name.endswith('.c4')])
            c_loc = sum([f.lines_in_file for f in files_list if f.name.endswith('.c')])
            h_loc = sum([f.lines_in_file for f in files_list if f.name.endswith('.h')])
            inl_loc = sum([f.lines_in_file for f in files_list if f.name.endswith('.c4')])
            print("Files,Num of Files, LoC")
            print(f"ucx all,{total_files},{lines_of_code}")
            print(f"ucx c_only,{c_files},{c_loc}")
            print(f"ucx h_only,{h_files},{h_loc}")
            print(f"ucx inl_only,{inl_files},{inl_loc}")
            for dir in files_dict.keys():
                sub_files_list = [f for f in files_list if f.name.startswith(dir)]
                total_files = len(sub_files_list)
                lines_of_code = sum([f.lines_in_file for f in sub_files_list])
                c_files = len([f.name for f in sub_files_list if f.name.endswith('.c')])
                h_files = len([f.name for f in sub_files_list if f.name.endswith('.h')])
                inl_files = len([f.name for f in sub_files_list if f.name.endswith('.c4')])
                c_loc = sum([f.lines_in_file for f in sub_files_list if f.name.endswith('.c')])
                h_loc = sum([f.lines_in_file for f in sub_files_list if f.name.endswith('.h')])
                inl_loc = sum([f.lines_in_file for f in sub_files_list if f.name.endswith('.c4')])
                print(f"{dir} all,{total_files},{lines_of_code}")
                print(f"{dir} c_only,{c_files},{c_loc}")
                print(f"{dir} h_only,{h_files},{h_loc}")
                print(f"{dir} inl_only,{inl_files},{inl_loc}")

    ############### MAIN WORKFLOW ###############
    executeClusterWorkflow(files_dict, algorithm, args.source_dir, output_dir, k_values,
                args.random_samples, tuple(args.directories), args.project, args.max_plot_depth)
    
