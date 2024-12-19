import re
import os
# ANTLR packages
from antlr_build.CLexer import CLexer
from antlr_build.CParser import CParser
from helperFunctions.ModuleExtractionListener import ModuleExtractionListener
from antlr4 import *

class FileNode():
    def __init__(self, source_dir, run_dir, file_name, joint_file=0):
        # File metadata
        self.name = file_name
        self.component = run_dir # UCT/UCP/UCS
        self.source_dir = source_dir
        self.full_path = source_dir + file_name
        self.parent_dir = os.path.dirname(self.full_path)

        # File data
        self.lines_in_file = 0
        self.file_dependencies = {} # key = file name, value = # of dependencies
        self.file_dependents = {}
        # Things defined outside the file
        self.macro_dependencies = []
        self.other_dependencies = []
        # Things defined within the file
        self.macro_definitions = []
        self.other_definitions = []
        
        if not joint_file:
            self.grepForDependencies()
    
    def print(self):
        print(f"Name: {self.name}")
        print(f"Lines in File: {self.lines_in_file}")
        print(f"File Dependencies: {self.file_dependencies}")
        print(f"File Dependants: {self.file_dependents}")
        #print(f"Macros Defs: {self.macro_definitions}")
        #print(f"Macros Calls: {self.macro_dependencies}")
        #print(f"Other Defs: {self.other_definitions}")
        #print(f"Other Calls: {self.other_dependencies}")
        print()
    
    def grepForDependencies(self):
        include_regex = re.compile(r'#include\s+["<](.*?)[">]')
        macro_regex = re.compile(r'#define\s+(\w+)\s*\(')

        # Get the include statements from the file line-by-line
        lines_count = 0
        with open(self.full_path, 'r') as f:
            for line in f:
                lines_count += 1
                include_match = include_regex.search(line)
                macro_match = macro_regex.search(line)
                if include_match:
                    include_file = include_match.group(1)
                    # Check how the path is defined
                    if os.path.exists(os.path.join(self.source_dir, include_file)):
                        full_path = os.path.abspath(os.path.join(self.source_dir, include_file))
                    elif os.path.exists(os.path.join(self.parent_dir, include_file)):
                        full_path = os.path.join(self.parent_dir, include_file)
                    else:
                        continue
                    # Verify that the resolved path exists
                    if os.path.isfile(full_path):
                        relative_path = os.path.realpath(full_path).replace(self.source_dir, "")
                        self.file_dependencies[relative_path] = 0
                elif macro_match:
                    macro = macro_match.group(1)
                    self.macro_definitions.append(macro)
        self.lines_in_file = lines_count

    def getAntlrDependencies(self):
        # ANTLR file stream
        input_stream = FileStream(self.full_path, encoding='utf-8')
        # Tokenize the strings and stream the tokens to the parser
        lexer = CLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = CParser(stream)
        # Build a tree from the C grammar's "translationUnit" rule
        tree = parser.translationUnit()
        # Walk the tree with the listener
        walker = ParseTreeWalker()
        result_lists = [self.other_definitions,
                        self.other_dependencies,
                        self.macro_dependencies]
        walker.walk(ModuleExtractionListener(result_lists), tree)

        # Helper function to remove internal dependencies from the lists
        def remove_list_commonalities(x, y):
            # Items in x will be removed from y
            for i in x[:]:
                if i in y:
                    y.remove(i)
        remove_list_commonalities(self.other_definitions, self.other_dependencies)
        remove_list_commonalities(self.macro_definitions, self.macro_dependencies)

    def shareDependencies(self, run_dirs, files_dict):
        for dependency in self.file_dependencies.keys():
            for run_dir in run_dirs:
                if dependency in files_dict[run_dir].keys():
                    dependency_obj = files_dict[run_dir][dependency]
                    dependency_obj.file_dependents[self.name] = self.file_dependencies[dependency]

    def resetDependencies(self):
        for key in self.file_dependencies.keys():
            self.file_dependencies[key] = 0
        for key in self.file_dependents.keys():
            self.file_dependents[key] = 0

class ClusterNode():
    def __init__(self, source_dir, cluster_path, cluster_index, files_list):
        # File metadata
        self.name = f'{cluster_path}:{cluster_index}'
        self.path = cluster_path
        self.index = cluster_index
        self.source_dir = source_dir

        # Cluster data
        self.mean_mq = 0
        self.files_list = {}
        # Add the nodes
        for file in files_list:
            self.addFile(file)

    def addFile(self, file):
        self.files_list[file.name] = file
    
    def getFileDependencies(self):
        return [file for file in self.files_list.values()]
    
    def print(self):
        print(f"Name: {self.name}")
        print(f"Files in cluster: {[f for f in self.files_list.keys()]}")
        print()

