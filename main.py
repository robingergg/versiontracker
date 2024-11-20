import os
import hashlib


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

    def target_exists(self, path: str):
        if os.path.exists(path):
            return True
        return False

    def init(self, vcs=None):

        vcs = vcs if vcs else MyVcs.vcs

        if os.path.exists(vcs):
            print("Inited already. Returning...")
            return

        dirs_to_add = [
            vcs,
            os.path.join(vcs, "objects"),
            os.path.join(vcs, "refs"),
            os.path.join(vcs, "refs", "heads"),
        ]

        for dir in dirs_to_add:
            if not self.target_exists(dir):
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


    def create_blob(self, file: str): # eg my.txt
        """ 
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
    
    def store_blob(self, content, hashed_blob):

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

    def read_file(self, file):
        try:
            with open(file, 'rb') as f:
                content = f.read()
                return content
        except Exception as e:
            print(e)

    def create_tree(self, files):
        """ 
        Create this foramt:
        tree <size-of-tree-in-bytes>\0
        <file-1-mode> <file-1-path>\0<file-1-blob-hash>
        <file-2-mode> <file-2-path>\0<file-2-blob-hash>
        ...
        <file-n-mode> <file-n-path>\0<file-n-blob-hash>
        """
        file_mode = "100655"
        content = ""
        tmp_content = ""
        # 1. prepare tree data
        for data in files:
            file_name = data[0]
            hashed_blob = data[1]
            tmp_content = f"{file_mode} {file_name}\x00"
            tmp_content += hashed_blob
        
        content = content.encode('utf-8')

        header = f"tree {len(content)}\x00".encode('utf-8')
        tree = header + content

        hashed_tree = hashlib.sha1(tree).hexdigest()

        print(tree, hashed_tree)
        return tree, hashed_tree

    def create_commit(self, hashed_tree, parent_commit="", author="Robin", msg="Initial commit"):

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
    
    def get_current_branch(self):
        curr_branch = None
        # Determine the absolute path to the HEAD file
        head_path = os.path.join(MyVcs.vcs, 'HEAD')
        abs_head_path = os.path.join(MyVcs.curr_workdir, head_path)
        # abs_head_path = os.path.abspath(head_path)
        
        try:
            with open(abs_head_path, "r") as f:
                curr_branch = f.read().strip()
                print(f"Current branch: {curr_branch}")
            f.close()
        except FileNotFoundError:
            print(f"Error: The file {abs_head_path} does not exist.")
        except Exception as e:
            print(f"An error occurred: {e}")
        
        return curr_branch
    
    def show_branches(self):
        curr_branch = self.get_current_branch()
        
        branches = os.listdir(".vcs/refs/heads")
        for b in branches:
            if b == curr_branch:
                print(f"\n{b} <-- HEAD")
            else:
                print(f"\n{b}")

    def stage_files(self, file):
        blob, hashed_blob = self.create_blob(file)
        # creating blob's path
        blob_dir = hashed_blob[:2]
        blob_file = hashed_blob[2:]
        blob_path = os.path.join(MyVcs.vcs, "objects", blob_dir, blob_file)

        if not self.target_exists(blob_path):
            self.store_blob(blob, hashed_blob)
        else:
            print(f"No changes made to: {file}")
            return

        curr_idx = f"{file} {hashed_blob}"

        # show files ,that has been changed
        self.display_changed_files()


        with open(f"{MyVcs.vcs}/index", "r") as f:
            index_content = f.read()

        if hashed_blob not in index_content:
            index_content += f"{curr_idx}\n"
            with open(f"{MyVcs.vcs}/index", "w") as f:
                f.write(index_content)
        else:
            print(f"\nAlready staged: {file}")

    def display_changed_files(self):
        latest_commit = self.get_branch_latest_commit(self.get_current_branch())

        if latest_commit:
            stored_parent_commit, stored_message, tree_hash = self.get_parent_attributes(latest_commit)
            self.show_modified_objects(tree_hash)
        else:
            print("Error: no latest commit.")

    def get_parent_attributes(self, commit):
        dir_path = commit[:2]
        file_path = commit[2:]

        stored_parent_commit = None
        stored_message = None
        tree_hash = None

        m_path = os.path.join(MyVcs.vcs, "objects", dir_path, file_path)
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
    
    def show_modified_objects(self, tree_hash):
        in_index = False
        dir_path = tree_hash[:2]
        file_path = tree_hash[2:]
        changed_files = []
        m_path = ".vcs/" + "objects/" + dir_path + "/" + file_path

        if not tree_hash:
            print("No tree hash.. return...")
            return
        
        all_dirs, all_files = self.get_all_dirs_in_repo()

        with open(m_path, "rb") as f:
            content = f.read()
            content = content.split(b'\x00')

            for i in range(len(content)):
                elem = content[i]
                elem = elem.decode().split(" ")
                if isinstance(elem, list) and len(elem) > 1:
                    elem = elem[1]
                if elem in all_files: 
                    stored_hash = content[i+1].strip().decode('utf-8')
                    curr_hash = self.create_blob(elem)[1]
                    
                    if stored_hash != curr_hash:
                        index_content = self._get_staged()
                    
                        if index_content:
                            for cont in index_content:
                                if elem in cont:
                                    in_index = True
                                if not in_index:
                                    changed_files.append(elem)
                        else:
                            changed_files.append(elem)
                        
        print("Modified files:")
        for file in changed_files:
            print(file)
        
    def get_all_files_in_repo(self):
        files_list = []
        for root, dirs, files in os.walk('.'):
            if  [".vcs", "__pycache__"] not in dirs:
                files_list.extend(files)
        return files_list
    
    def get_all_dirs_in_repo(self):
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
        index_content = None
        with open(f"{MyVcs.vcs}/index", "r") as f:
            index_content = f.readlines()
        return index_content

    def show_staged_files(self) -> None:
        index_content = self._get_staged()
        print("\nStaged files\n-----------------")
        for line in index_content:
            print(f"STAGED: {line.split()[0]}")

    def get_branch_latest_commit(self, branch):
        curr_branch_path = os.path.join(MyVcs.curr_workdir, MyVcs.vcs, f"refs/heads/{branch}")
        print(f"Attempting to open branch file at: {curr_branch_path}")
        
        if not os.path.exists(curr_branch_path):
            raise FileNotFoundError(f"Branch file does not exist at: {curr_branch_path}")
        
        try:
            with open(curr_branch_path, "r") as f:
                latest_commit = f.read().strip()
                print(f"Latest commit: {latest_commit}")
                if not latest_commit:
                    raise ValueError("Latest commit could not be read.")
            f.close()
            return latest_commit
        except Exception as e:
            print(f"Error reading branch file: {e}")
            raise

    def get_commit_id_from_curr_branch(self):
        curr_branch = self.get_current_branch()
        return self.get_branch_latest_commit(curr_branch)

    def update_latest_commit_in_curr_branch(self, commit_hash):
        branch = self.get_current_branch()
        with open(f"{MyVcs.vcs}/refs/heads/{branch}", "w") as f:
            return f.write(commit_hash)
        
    def make_commit(self, message: str = None):
        with open(f"{MyVcs.vcs}/index", "r") as f:
            index_content = f.readlines()
            print(f"cont of ind: {index_content}, {not index_content}")
            if not index_content:
                print("Nothing to commit.")
                return
        index_content = [line.strip() for line in index_content]
        # process string to file name and blob hash
        index_content = [[line.split()[0], line.split()[1]] for line in index_content]
        tree, hashed_tree = self.create_tree(index_content)
        self.store_blob(tree, hashed_tree)

        latest_commit = self.get_commit_id_from_curr_branch()

        commit, hashed_commit = self.create_commit(hashed_tree, parent_commit=latest_commit, msg=message)

        self.store_blob(commit, hashed_commit)

        # empty staging area
        with open(f"{MyVcs.vcs}/index", "w") as f:
            f.write("")

        # update latest commit in curr branch
        self.update_latest_commit_in_curr_branch(hashed_commit)

    def read_tree(tree: bytes) -> list[list]:
        read_vals = []
        tree = tree.decode()
        tree = tree.split("\n")
        for line in tree:
            curr_elem = []

            if not line:
                continue
            
            splitted = line.split("\x00")

            if "tree" in splitted[0]:
                curr_elem.append(splitted[1].split(" ")[1])
                curr_elem.append(splitted[2])
                read_vals.append(curr_elem)
            else:
                curr_elem.append(splitted[0].split(" ")[1])
                curr_elem.append(splitted[1])
                read_vals.append(curr_elem)

        return read_vals

    def read_commit(self, m_hash):
        pass

    def show_vcs_tree(self):
        latest_commit = self.get_commit_id_from_curr_branch()
        # open latest commit
        self.show_all_commits(latest_commit)

    def show_all_commits(self, commit):
        stored_parent_commit = None
        stored_message = None

        while commit:
            stored_parent_commit, stored_message, tree_hash = self.get_parent_attributes(commit)
    
            print(f"({commit}) - {stored_message}")
            commit = stored_parent_commit
            # return stored_parent_commit
            
    def read_hash(self, hash, callback, all_comm, all_msgs):

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
                self.read_hash(parent_commit, callback, all_comm, all_msgs)

    def display_commit_tree(self):
        all_comm = []
        all_msgs = []

        def collect_commits(all_comm, commit, all_msgs, msg):
            all_comm.append(commit)
            all_msgs.append(msg)

        curr_commit_id = self.get_commit_id_from_curr_branch()
        self.read_hash(curr_commit_id, collect_commits, all_comm, all_msgs)

        for i in range(0, len(all_comm)):
            commit = all_comm[i]
            msg = all_msgs[i]

            if commit == curr_commit_id:
                print(f"{commit} - {msg} <- HEAD")
            else:
                print(f"{commit} - {msg}")
