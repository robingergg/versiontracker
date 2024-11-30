import os
import hashlib
from typing import Union
from colorama import Fore, Back, Style


"""
Example usage:

file_1 = "my.txt"

vcs.init()

vcs.display_changed_files()
vcs.stage_files(file_1)
vcs.make_commit()
"""

all_commit = []


class MyVcs:

    vcs = ".vcs/"
    obj_path = os.path.join(vcs, "objects")
    curr_workdir = "/home/robin/programming/versiontracker/"

    def log_msg(self, msg: str, op: str):
        if op == "i":
            print(f"INFO\t{msg}")
        elif op == "d":
            print(f"DEBUG\t{msg}")
        elif op == "e":
            print(f"ERROR\t{msg}")
        elif op == "w":
            print(f"WARN\t{msg}")

    def _target_exists(self, path: str) -> bool:
        """
        Checks whether a selected file or directory exists.
        """
        if os.path.exists(path):
            return True
        return False

    def init(self, vcs=None):
        """
        Initializes the tracking systems root directory where all objects will be stored,
        such as refs, heads, objects, index.
        """
        vcs = vcs if vcs else MyVcs.vcs

        if os.path.exists(vcs):
            print("Inited already. Returning...")
            return

        dirs_to_add = [
            vcs,
            MyVcs.obj_path,
            os.path.join(vcs, "refs"),
            os.path.join(vcs, "refs", "heads"),
        ]

        for dir in dirs_to_add:
            if not self._target_exists(dir):
                os.mkdir(dir)
            else:
                self.log_msg(f"Target already exists: {dir}", "e")

        if not os.path.exists(os.path.join(vcs, "HEAD")):
            with open(os.path.join(vcs, "HEAD"), "w") as f:
                f.write("main")

        if not os.path.exists(os.path.join(vcs, "index")):
            with open(f"{MyVcs.vcs}/index", "w") as f:
                f.write("")

        if not os.path.exists(os.path.join(vcs, "refs", "heads", "main")):
            with open(os.path.join(vcs, "refs", "heads", "main"), "w") as f:

                commit, hashed_commit = self.create_commit("", parent_commit="", msg="First(init) Commit")
                self.store_blob(commit, hashed_commit)
                f.write(hashed_commit)

    def create_file_blob(self, file: str): # eg my.txt
        """ 
        Creates a blob for a file.
        Create this foramt:
        blob <size-of-blob-in-bytes>\0<file-binary-data>
        """
        content = None
        content_size = None

        # 1. read file content as binary    eg.: "hello"
        with open(file, 'rb') as f:
            content = f.read()
            content_size = len(content)

        # 2. create the blob
        header = f"blob {content_size}\0".encode('utf-8')
        blob = header + content

        # 2. hash the file content
        hashed_blob = hashlib.sha1(blob).hexdigest()

        return blob, hashed_blob
    
    def store_blob(self, content: str, hashed_blob: str):
        """
        Stores the content of a blob and 
        he blob itself into objects directory.
        """
        # 1. slice hashed_blob
        dir_path = os.path.join(MyVcs.vcs, "objects", hashed_blob[:2])
        blob_path = os.path.join(dir_path, hashed_blob[2:])

        # 2. create blob dir
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        else:
            print(f"Error: path exists: {dir_path}")

        # 3. save to objects dir
        with open(blob_path, 'wb') as f:
            f.write(content)

    def create_tree(self, files):
        """ 
        Createsa tree object.
        Create this foramt:
        tree <size-of-tree-in-bytes>\0
        <file-1-mode> <file-1-path>\0<file-1-blob-hash>
        <file-2-mode> <file-2-path>\0<file-2-blob-hash>
        ...
        <file-n-mode> <file-n-path>\0<file-n-blob-hash>
        """
        file_mode = "100655" # TODO: do not hard code it, but make it flexible
        content = b""
        tmp_content = ""
        # 1. prepare tree data
        for data in files:
            file_name = data[0]
            hashed_blob = data[1]
            tmp_content += f"{file_mode} {file_name}\x00"
            # if it is 40 character long it means it hasnt
            # been extended with a new line character as a separator
            if len(hashed_blob) == 40:
                tmp_content += hashed_blob + "\n"
            else:
                tmp_content += hashed_blob

        content += tmp_content.encode('utf-8')
        header = f"tree {len(content)}\x00".encode('utf-8')
        tree = header + content
        hashed_tree = hashlib.sha1(tree).hexdigest()

        return tree, hashed_tree

    def create_commit(self, hashed_tree: str, parent_commit: str = "",
                      author: str = "Robin", msg: str = "Initial commit"):
        """
        Creates a commit object, containing tree, parent, author and message.
        """
        # building commit contnet
        commit_content = ""
        commit_content += f"tree {hashed_tree}\n"
        commit_content += f"parent {parent_commit}\n"
        commit_content += f"author {author}\n"
        commit_content += f"message {msg}\n"

        commit_content = commit_content.encode('utf-8')
        commit_content_lngth = len(commit_content)

        commit_header = f"commit {commit_content_lngth}\x00".encode('utf-8')
        commit = commit_header + commit_content

        hashed_commit = hashlib.sha1(commit).hexdigest()

        return commit, hashed_commit
    
    def get_current_branch(self) -> str:
        """
        Returns the name of the current branch,
        the branch to which the head points to.
        """
        curr_branch = None
        # Determine the absolute path to the HEAD file
        head_path = os.path.join(MyVcs.vcs, 'HEAD')
        abs_head_path = os.path.join(MyVcs.curr_workdir, head_path)
        # abs_head_path = os.path.abspath(head_path)
        
        try:
            with open(abs_head_path, "r") as f:
                curr_branch = f.read().strip()
            f.close()
        except FileNotFoundError:
            print(f"Error: The file {abs_head_path} does not exist.")
        except Exception as e:
            print(f"An error occurred: {e}")
        
        return curr_branch
    
    def stage_file(self, file: str):
        """
        Creates blob of a selected file and puts it into the index.
        """
        index_content = None

        blob, hashed_blob = self.create_file_blob(file)
        # creating blob's path
        blob_dir = hashed_blob[:2]
        blob_file = hashed_blob[2:]
        blob_path = os.path.join(MyVcs.vcs, "objects", blob_dir, blob_file)

        if not self._target_exists(blob_path):
            self.store_blob(blob, hashed_blob)
        else:
            print(f"No changes made to: {file}")
            return

        curr_idx = f"{file} {hashed_blob}"

        # show files, that has been modified
        self.display_modified_files()

        with open(f"{MyVcs.vcs}/index", "r") as f:
            index_content = f.read()

        if hashed_blob not in index_content:
            index_content += f"{curr_idx}\n"
            with open(f"{MyVcs.vcs}/index", "w") as f:
                f.write(index_content)
        else:
            print(f"\nAlready staged: {file}")

    def display_modified_files(self):
        """
        Shows the modified files in the repository based on the current branch.
        """
        latest_commit = self.get_branch_latest_commit(self.get_current_branch())

        if latest_commit:
            stored_parent_commit, stored_message, tree_hash = self.get_commit_attributes(latest_commit)
            self.show_modified_objects(tree_hash)
        else:
            print("Error: no latest commit.")

    def get_commit_attributes(self, commit_hash: str) -> tuple:
        """
        Reads a commit content by it's hash and get's it's attributes,
        such as parent, message, tree.
        """
        dir_path = commit_hash[:2]
        file_path = commit_hash[2:]

        stored_parent_commit = None
        stored_message = None
        tree_hash = None

        m_path = os.path.join(MyVcs.obj_path, dir_path, file_path)
        with open(m_path, "rb") as f:
            content = f.read()
            content = content.decode('utf-8').split("\n")
            for line in content:
                if "parent" in line:
                    stored_parent_commit = line.split(" ")[1]
                elif "message" in line:
                    stored_message = " ".join(line.split(" ")[1:])
                elif "tree" in line:
                    tree_hash = line.split(" ")[-1]

        return stored_parent_commit, stored_message, tree_hash
    
    def show_modified_objects(self, tree_hash: str):
        """
        Prints the modified files. Modified files are the ones
        which hashes are different now, than it is in the objects directory.
        """
        if not tree_hash:
            print("No tree hash. Return...")
            return

        modified_files = []

        dir_path = tree_hash[:2]
        file_path = tree_hash[2:]
        tree_path = os.path.join(MyVcs.obj_path, dir_path, file_path)
        
        all_dirs, all_files = self._get_all_dirs_and_files_in_repo()

        with open(tree_path, "rb") as f:
            tree_content = f.read()
            tree_content = tree_content.split(b'\x00', 1)
            if b"tree" in tree_content[0]:
                tree_content = tree_content[1:][0].split(b'\n')

            for i in range(len(tree_content)):
                split_tree_cont = tree_content[i]
                if not split_tree_cont:
                    continue
                split_tree_cont = split_tree_cont.decode().split(" ")[1].split("\x00")
                file = split_tree_cont[0]
                stored_hash = split_tree_cont[1]
                if isinstance(file, list) and len(file) > 1:
                    file = file[1]
                    
                if file in all_files: 
                    # stored_hash = tree_content[i+1].strip().decode('utf-8')
                    curr_hash = self.create_file_blob(file)[1]
                    
                    if stored_hash != curr_hash:
                        index_content = self._get_staged()
                    
                        if index_content:
                            for idx_cont in index_content:
                                in_index = False
                                if file in idx_cont:
                                    in_index = True
                                if not in_index:
                                    modified_files.append(file)
                        else:
                            modified_files.append(file)
                        
        print("Modified files:")
        for file in modified_files:
            print(file)
        
    def _get_all_dirs_and_files_in_repo(self) -> tuple:
        """
        Gets all dirs and files in the repo.
        Exludes files/ dirs given. TODO: make it configurable.
        """
        dir_list = []
        file_list = []

        for root, dirs, files in os.walk('.'):
            inside_root = any([elem in root for elem in [".venv", ".vcs", ".git", ".vscode", "__pycache__"]])
            if not inside_root:
                for dir in dirs:
                    if dir not in [".venv", ".vcs", ".git", ".vscode", "__pycache__"]:
                        dir_list.append(dir)
                for file in files:
                    if file not in [".gitignore"]:
                        file_list.append(file)
        return dir_list, file_list
    
    def _get_staged(self) -> list:
        """
        Returns the staged files in a list.
        """
        index_content = None
        with open(f"{MyVcs.vcs}/index", "r") as f:
            index_content = f.readlines()
        return index_content

    def show_staged_files(self) -> None:
        """
        Displays all staged files.
        """
        index_content = self._get_staged()
        print("\nStaged files\n-----------------")
        for line in index_content:
            print(f"STAGED: {line.split()[0]}")

    def get_branch_latest_commit(self, branch: str) -> Union[str, None]:
        """
        Gets the latest commit from the current branch.
        """
        latest_commit = None

        curr_branch_path = os.path.join(MyVcs.curr_workdir, MyVcs.vcs, f"refs/heads/{branch}")
        if not os.path.exists(curr_branch_path):
            raise FileNotFoundError(f"Branch file does not exist at: {curr_branch_path}")
        try:
            with open(curr_branch_path, "r") as f:
                latest_commit = f.read().strip()
                if not latest_commit:
                    raise ValueError("Latest commit could not be read.")
            return latest_commit
        except Exception as e:
            raise ValueError(f"Error reading branch file: {e}")

    def get_commit_id_from_curr_branch(self) -> str:
        """
        Returns the latest commit id form the current branch.
        """
        curr_branch = self.get_current_branch()
        return self.get_branch_latest_commit(curr_branch)

    def update_latest_commit_in_curr_branch(self, commit_hash: str) -> str:
        """
        Updates the latest commit in the current branch.
        """
        branch = self.get_current_branch()
        with open(f"{MyVcs.vcs}/refs/heads/{branch}", "w") as f:
            return f.write(commit_hash)
        
    def make_commit(self, message: str = None) -> None:
        """
        Creates a commit using the files stored in index.
        """
        with open(f"{MyVcs.vcs}/index", "r") as f:
            index_content = f.readlines()
            if not index_content:
                print("Nothing to commit.")
                return
            
        current_commit_content = self.get_all_files_and_hashes_in_commit(self.get_branch_latest_commit(self.get_current_branch()))
        # if current commit content is mepty (initial commit) then make it an empty list
        if not current_commit_content:
            current_commit_content = []

        # removing new line command from content
        current_commit_content = [[line.strip("\n") for line in block] for block in current_commit_content]

        index_content = [line.strip() for line in index_content]
        # process string to file name and blob hash
        index_content = [[line.split()[0], line.split()[1]] for line in index_content]

        # check if a given file is in the current commit content, and if so,
        # remove it and append the staged version instead.
        # This is important because the same file/ content can be part of the previous commit as well as the index area
        # (change made in file.txt). In this case we want to keep the staged version because that is the latest version of the file.
        merged_dict = {item[0]: item for item in current_commit_content}
        merged_dict.update({item[0]: item for item in index_content})
        cleaned_entries = list(merged_dict.values())

        tree, hashed_tree = self.create_tree(cleaned_entries)
        self.store_blob(tree, hashed_tree)

        latest_commit = self.get_commit_id_from_curr_branch()
        commit, hashed_commit = self.create_commit(hashed_tree, parent_commit=latest_commit, msg=message)
        self.store_blob(commit, hashed_commit)

        # empty staging area
        with open(f"{MyVcs.vcs}/index", "w") as f:
            f.write("")

        # update latest commit in curr branch
        self.update_latest_commit_in_curr_branch(hashed_commit)

    def _read_tree_obj(self, tree: Union[list[bytes, str]]) -> list[list]:
        """
        From a tree line it gets the file
        name and it's blob and returns it.

        Returns:
            [<file_name>, <content_hash>]
        """
        read_vals = []

        for line in tree:
            if isinstance(line, bytes):
                line = line.decode()

            if not line:
                continue
            
            splitted = line.split("\x00", 1)[1].split("\n")

            for data in splitted:
                if data:
                    file_name, file_hash = data.split(" ")[1].split("\x00")
                    elem = [file_name, file_hash]
                    read_vals.append(elem)

        return read_vals
    
    def read_file_content(self, file_content: list) -> None:
        """
        Reads the content of a list of files.
        Used with: read_tree_obj()
        Example input: 
            [["my.txt", <file hash>], ["my_2.txt", <file hash>]]
        """
        for file in file_content:
            file_name = file[0]
            blob = file[1]
            cont = self.get_blob_content(blob)
            print(cont.decode())

    def _get_tree_content_from_commit_hash(self, commit_hash: Union[bytes, str]) -> Union[list, None]:
        """
        Takes a commit hash and returns it's tree content,
        eg: ['tree 54\x00100655 my.txt\x00965b616c94adf9144531acc13aada5bd1ee05018']

        Suggestion: read_tree_content()
        """
        tree_hash = self.get_tree_hash_from_commit(commit_hash)
        if not tree_hash:
            return None
        tree_content = self.get_blob_content(tree_hash)
        return tree_content
    
    def read_tree_content(self, tree_obj: bytes) -> list[list[str, str]]:
        """
        Takes a tree object, eg: b'tree 55\x00100655 my.txt\x002427deaa4f262d9d1d5981e3a7094de0546bc48f\n'
        and returns all file names and corresponding blobs.

        Suggestion: use it with _get_tree_content_from_commit_hash()
        """
        collected_file_names_and_contnet = []

        # split tree from the rest of the content
        tree_obj = tree_obj.decode()
        tree_obj = tree_obj.split("\x00", 1)[1]

        # split each file entry by new line char
        tree_obj = tree_obj.split("\n")

        # extract filenames and contents
        for entry in tree_obj:
            if entry:
                entry = entry.split(" ", 1)[1] # extract the filename and contnet part
                file_name = entry.split("\x00")[0]
                file_content = entry.split("\x00")[1]
                collected_file_names_and_contnet.append([file_name, file_content])

        # return list
        return collected_file_names_and_contnet

    
    def get_tree_hash_from_commit(self, commit_blob: bytes) -> Union[str, None]:
        """
        Takes a commit id and gets the commit value from it,
        then it extracts the tree hash out of it.

        Example input value:
            b'commit 121\x00tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904\nparent
            8d8b4007631d052e389906f9fde44fba6334798e\nauthor Robin\nmessage first\n'
        """
        tree_hash = None
        ret = self.get_blob_content(commit_blob)
        if ret:
            if isinstance(ret, bytes):
                ret = ret.decode()
            splitted_commit_val = ret.split('\n')
            tree_hash = splitted_commit_val[0].split(" ")[-1]
        if tree_hash:
            return tree_hash
        return None

    def _read_hash(self, hash, callback, all_comm, all_msgs):
        """
        Reads the given commit's content and,
        all parent commit's content recursively.
        Used for display_commit_tree() to display all commits for the commit tree.
        """
        if not hash:
            print("No hash given. Returning...")
            return

        dir_path = os.path.join(MyVcs.vcs, "objects", hash[:2])
        blob_path = os.path.join(dir_path, hash[2:])

        with open(blob_path, "r") as f:
            content = f.read()
            content = content.split("\n")
        f.close()
        
        parent_comm = None
        message = None
        parent_commit = None
        for line in content:
            if "parent" in line:
                parent_commit = line.split(" ")[1]

            elif "message" in line:
                message = " ".join(line.split(" ")[1:])

            if not line:
                # parent_comm = parent_commit
                callback(all_comm, hash, all_msgs, message)
                # callback(all_comm, parent_commit, all_msgs, message)
                self._read_hash(parent_commit, callback, all_comm, all_msgs)

    def get_blob_content(self, blob: Union[bytes, str]) -> bytes:
        """Gets any blob/hash, reads it and returns it's content."""
        content = None

        dir_path = os.path.join(MyVcs.obj_path, blob[:2])
        blob_path = os.path.join(dir_path, blob[2:])

        with open(blob_path, "rb") as f:
            content = f.read()

        if content:
            return content
        raise ValueError(f"No content value could be read from blob: {blob}")

    def display_commit_tree(self):
        """
        Displays the commit log (git log --graph --oneline) recurseivly.
        It takes the current commit id which can be the latest commit or a parent commit
        and with a help of a callback function it iterates over all subsequent parent commit hash
        and displays it, inicating where the HEAD is. 
        """
        all_comm = []
        all_msgs = []

        def collect_commits(all_comm, commit, all_msgs, msg):
            all_comm.append(commit)
            all_msgs.append(msg)

        curr_commit_id = self.get_commit_id_from_curr_branch()
        self._read_hash(curr_commit_id, collect_commits, all_comm, all_msgs)

        for i in range(0, len(all_comm)):
            commit = all_comm[i]
            msg = all_msgs[i]

            if commit == curr_commit_id:
                print(f"{commit} - {msg} <- HEAD")
            else:
                print(f"{commit} - {msg}")

    def get_all_files_and_hashes_in_commit(self, commit_hash: str) -> Union[list, None]:
        """
        Takes a commit id, reads it's tree object and returns 
        all files included in that tree object.
        """
        tree_hash_from_commit = self.get_tree_hash_from_commit(commit_hash)
        if not tree_hash_from_commit:
            return None
        tree_hash_content = self.get_blob_content(tree_hash_from_commit)
        tree_hash_content = [tree_hash_content]
        tree_obj_content = self._read_tree_obj(tree_hash_content)

        return tree_obj_content
    
    def ammend(self, message: str = None):
        """
        Gets the latest commit and it's content
        """
        latest_commit = self.get_branch_latest_commit(self.get_current_branch())

        index_content = self._get_staged()
        index_content = self._organize_index_content_into_nested_list(index_content)

        # get the current latest commits attribute to update the new ammended commit with it
        parent_commit, stored_message, tree_hash = self.get_commit_attributes(latest_commit)
        
        # create a new tree object
        tree, tree_blob = self.create_tree(index_content)
        self.store_blob(tree, tree_blob)

        # if got new message, assign it
        if not message:
            message = stored_message

        # create a new commit object
        commit, commit_hash = self.create_commit(hashed_tree=tree_blob, parent_commit=parent_commit, msg=message)
        self.store_blob(commit, commit_hash)

        # update current branch with the latest commit
        self.update_latest_commit_in_curr_branch(commit_hash)

    def _organize_index_content_into_nested_list(self, index_content) -> list[list[str]]:
        """
        _get_staged() returns a list of modified items, but
        for further processing we need them separately inside
        a nested list, containing like this: [[<file_name>, <file_hash>]]
        """
        tmp_inx_cont = []
        for cont in index_content:
            tmp_inx_cont.append(cont.split(" "))
        return tmp_inx_cont

    def read_commit_differences(self, commit_hash_1: str, commit_hash_2: str):
        """
        Given two commit hash, it will first extract the trees inside them, then
        get all files, and hteir contents and compare them and log any difference.
        """
        if commit_hash_1 == commit_hash_2:
            print("No difference...")
            return

        tree_content_1 = self.get_all_files_and_hashes_in_commit(commit_hash_1)
        tree_content_2 = self.get_all_files_and_hashes_in_commit(commit_hash_2)

        if not tree_content_1 and tree_content_2:
            files_content_info = self.read_content_of_files(tree_content_2)
            for file_block in files_content_info:
                file_name = file_block[0]
                file_content = file_block[1].decode() if isinstance(file_block[1], bytes) else file_block[1]
                print(f"Difference for '{file_name}':")
                print(Fore.GREEN + file_content + Style.RESET_ALL) # text color/reset

        elif tree_content_1 and tree_content_2:
            files_content_info_1 = self.read_content_of_files(tree_content_1)
            files_content_info_2 = self.read_content_of_files(tree_content_2)

            files_content_info_2 = self.search_for_block_difference(files_content_info_1, files_content_info_2)
            # If anymore file(s) left in the second block content then process it
            if files_content_info_2:
                self.search_for_block_difference(files_content_info_2, files_content_info_1)

    def search_for_block_difference(self, files_content_info_1: list[list[str, bytes]],
                                    files_content_info_2: list[list[str, bytes]]) -> list:
            """
            Searches for differences between two block, which are made from commits -> trees.
            """
            for file_block_1 in files_content_info_1:

                file_name_1 = file_block_1[0]
                file_content_1 = file_block_1[1]

                file_present = self.search_for_file_in_other_file_block(file_name_1, files_content_info_2)

                # print out new file attributes
                if not file_present:
                    print("New file:")
                    print(Fore.GREEN + f"{file_name_1}:")
                    print(file_content_1.decode() + Style.RESET_ALL)
                # print out the differences
                else:
                    file_content_2 = self.get_content_by_file_name(file_name_1, files_content_info_2)
                    if file_content_1 != file_content_2:

                        print()
                        print(f"Difference of '{file_name_1}' are:")
                        print(Fore.RED + f"- {file_content_1.decode()}")
                        print(Fore.GREEN + f"+ {file_content_2.decode()}" + Style.RESET_ALL) # reset text color
                
                # filter out each file which has been processed
                files_content_info_2 = [
                    block for block in files_content_info_2 
                    if block[0] != file_name_1
                ]

            return files_content_info_2

    def get_content_by_file_name(self, file_name: str,
                                 files_content_info_2: list) -> Union[str, None]:
        """
        Gets the contnet of a file by it's file name.
        Used for getting info from file blocks when asserting differences.
        """
        for file_block_2 in files_content_info_2:
            file_name_2 = file_block_2[0]
            file_content_2 = file_block_2[1]

            if file_name == file_name_2:
                return file_content_2
        return None

    def search_for_file_in_other_file_block(self, file_name: str, files_content_info: list) -> bool:
        """
        Searches for a given file by it's name in an other file info block,
        generated by reading the contents of a tree.
        """
        for file_block in files_content_info:
            if file_name in file_block:
                return True
        return False

    def read_content_of_files(self, files_content: list[list[str, str]]) -> list[list[str, str]]:
        """
        Reads each files content in the list.
        Example input: [[<file_name_1>, <file_hash_1>], [<file_name_1>, <file_hash_1>]]
        """
        files_informations = []
        for file_content_pair in files_content:
            file_name = file_content_pair[0]
            file_hash = file_content_pair[1].strip("\n")

            file_content = self.get_blob_content(file_hash)
            file_content = self._get_content_from_blob(file_content)

            files_informations.append([file_name, file_content])

        return files_informations

    def _get_content_from_blob(self, blob: str) -> str:
        """
        Returns the actual contnet of a blob (file).
        """
        indicator = blob.split(b"\x00")[0]
        blob_type = indicator.split(b" ")[0]
        contnet_lngth = indicator.split(b" ")[1]
        
        content = blob.split(b"\x00")[1]
        return content
    
    def reset_hard(self, commit_hash: str) -> None:
        # tree_object_content = self.get_all_files_and_hashes_in_commit(commit_hash)
        # print(tree_object_content)
        tree_content = self._get_tree_content_from_commit_hash(commit_hash)
        print(tree_content)

        files_and_hashes = self.read_tree_content(tree_content)
        print(files_and_hashes)

        # go thru on each file, read contnet and write it
        # get file names and actual contents
        files_contents = self.read_content_of_files(files_and_hashes)
        print("FILE CONTENTS: ", files_contents)

        # loop thru each fileand overide it's content
        for content_block in files_contents:
            file_name = content_block[0]
            file_content = content_block[1]

            # check what type of content the file has and write
            # the contnet based on the reset accordingly
            writeing_mode = ""
            if isinstance(file_content, bytes):
                writeing_mode = "wb"
            elif isinstance(file_content, str):
                writeing_mode = "w"
            with open(file_name, writeing_mode) as f:
                f.write(file_content)

        # update HEAD
        self.update_latest_commit_in_curr_branch(commit_hash)
