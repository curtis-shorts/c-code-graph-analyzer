import os
import helperFunctions.nodesStructs as nodesStructs
from contextlib import redirect_stderr

def reconstrainFileReferences(run_dirs, files_dict, constraint):
    files_list = [file for sub_dict in files_dict.values() for file in sub_dict.values()]
    # Reset the file dependencies
    for file_i in files_list:
        file_i.resetDependencies()
    # Cross-compare the files to get inter-file dependencies
    for file_i in files_list:
        file_dependencies = file_i.file_dependencies
        for file_j_key in file_dependencies:
            file_j = ''
            # Get the object
            for run_dir in run_dirs:
                if file_j_key in files_dict[run_dir]:
                    file_j = files_dict[run_dir][file_j_key]
            if file_j == '':
                continue
            # Check macro dependencies
            if constraint == 'macros':
                for macro in file_i.macro_dependencies:
                    if macro in file_j.macro_definitions:
                        file_dependencies[file_j_key] += 1
            # Check function dependencies
            if constraint == 'functions':
                for other in file_i.other_dependencies:
                    if other in file_j.other_definitions:
                        file_dependencies[file_j_key] += 1

def crossReferenceFiles(files_list, run_dirs, files_dict):
    # Cross-compare the files to get inter-file dependencies
    for file_i in files_list:
        file_dependencies = file_i.file_dependencies
        for file_j_key in file_dependencies:
            file_j = ''
            # Get the object
            for run_dir in run_dirs:
                if file_j_key in files_dict[run_dir]:
                    file_j = files_dict[run_dir][file_j_key]
            if file_j == '':
                continue
            # Check macro dependencies
            for macro in file_i.macro_dependencies:
                if macro in file_j.macro_definitions:
                    file_dependencies[file_j_key] += 1
            # Check function dependencies
            for other in file_i.other_dependencies:
                if other in file_j.other_definitions:
                    file_dependencies[file_j_key] += 1

def getCAndHFilesHelper(directory):
    # Helper function to get a list of .c and .h files in a directory
    c_and_h_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.c', '.h', '.inl')):
                c_and_h_files.append(os.path.join(root, file))
    return c_and_h_files

def getFileDependencies(source_dir, run_dirs, antlr_err_outputs):
    # Get the file data for every file in the source directory
    # Files will be hashed based on the run directories
    files_dict = {}
    
    # Do a preliminary pass of every file to get their names
    # Also collects pre-processor statements (include files and defined macros)
    for run_dir in run_dirs:
        files_dict[run_dir] = {}
        component_directory = source_dir + run_dir
        files_list = getCAndHFilesHelper(component_directory)
        # Get the data for each file
        for file in files_list:
            file_name = file.replace(source_dir, "")
            file_object = nodesStructs.FileNode(source_dir, run_dir, file_name)
            files_dict[run_dir][file_name] = file_object
    
    # Get the remainder of intra-file data using ANTLR
    print("Extracting ANTLR data.")
    all_files = [file for sub_dict in files_dict.values() for file in sub_dict.values()]
    with open(antlr_err_outputs, 'w') as f:
        with redirect_stderr(f):
            for file in all_files:
                file.getAntlrDependencies()
    print("ANTLR data extraction complete.")

    # Get the dependencies between the files
    crossReferenceFiles(all_files, run_dirs, files_dict)
    for file in all_files:
        file.shareDependencies(run_dirs, files_dict)
    
    return files_dict

