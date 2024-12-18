import os
import helperFunctions.nodesStructs as nodesStructs

def joinCAndHFiles(files_dict, source_dir):
    joint_files_dict = {}
    all_files_list = [file for sub_dict in files_dict.values() for file in sub_dict.values()]
    # Join each of the file pairs
    seen_files = []
    for run_dir in files_dict.keys():
        joint_files_dict[run_dir] = {}
        for file_h_name in files_dict[run_dir].keys():
            if file_h_name.endswith(".h"):
                files_list = []
                seen_files.append(file_h_name)
                # Setup file name strings
                file_root = file_h_name.replace(".h", "")
                h_file = files_dict[run_dir][file_h_name]
                files_list.append(h_file)
                file_c_name = file_root + ".c"
                file_inl_name = file_root + ".inl"
                # Check if the .c file exists
                if os.path.exists(os.path.join(source_dir, file_c_name)):
                    seen_files.append(file_c_name)
                    files_list.append(files_dict[run_dir][file_c_name])
                # Check if the .inl file exists
                if os.path.exists(os.path.join(source_dir, file_inl_name)):
                    seen_files.append(file_inl_name)
                    files_list.append(files_dict[run_dir][file_inl_name])
                if len(files_list) < 2:
                    joint_files_dict[run_dir][file_h_name] = h_file
                    continue
                # Join the objects
                cluster = nodesStructs.ClusterNode(source_dir, file_root, 0, files_list)
                joint_files_dict[run_dir][file_root] = cluster

    # Add the .c files that didn't have .h files
    for file in all_files_list:
        if file.name not in seen_files:
            joint_files_dict[run_dir][file.name] = file

    return joint_files_dict