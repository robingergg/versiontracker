import os
import hashlib
import zlib


"""
create blob():
    takes file
create_tree()
create_commit()
create_branch()
create_head() ?
"""

all_commit = []


class MyVcs:

    vcs = ".vcs/"

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
            # os.path.join(vcs, "refs", "heads", "main"),
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
                f.write("")


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
            # tmp_content = f"{file_mode} {file_name}\x00".encode('utf-8')
            tmp_content = f"{file_mode} {file_name}\x00"
            tmp_content += hashed_blob
            # tmp_content = tmp_content + bytes.fromhex(hashed_blob)
            content += f"{tmp_content}\n"
        
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
        with open(f"{MyVcs.vcs}/HEAD", "r") as f:
            return f.read()
    
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
            print(f"File: {file} has already been stored...")

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
            print(content)
            for line in content:
                if "parent" in line:
                    stored_parent_commit = line.split(" ")[1]
                elif "message" in line:
                    stored_message = " ".join(line.split(" ")[1:])
                elif "tree" in line:
                    tree_hash = line.split(" ")[-1]

        return stored_parent_commit, stored_message, tree_hash
    
    def show_modified_objects(self, tree_hash):

        # go thru each file in the directory
        for root, dirs, files in os.walk('.'):

            changed_files = []

            dir_path = tree_hash[:2]
            file_path = tree_hash[2:]
            m_path = ".vcs/" + "objects/" + dir_path + "/" + file_path 
            # m_path = os.path.join(MyVcs.vcs, "objects", dir_path, file_path)
            with open(m_path, "rb") as f:
                content = f.read()
                # content = content.decode('utf-8').split("\n")
                content = content.split(b'\x00')

                all_files = self.get_all_files_in_repo()
                for i in range(len(content)):
                    elem = content[i]
                    elem = elem.decode().split(" ")
                    if isinstance(elem, list) and len(elem) > 1:
                        elem = elem[1]
                    if elem in all_files: 
                        stored_hash = content[i+1].strip().decode('utf-8')
                        curr_hash = self.create_blob(elem)[1]
                        
                        if stored_hash != curr_hash:
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

    def show_staged_files(self):
        with open(f"{MyVcs.vcs}/index", "r") as f:
            index_content = f.readlines()

            print("\nStaged files\n-----------------")
        for line in index_content:
            print(f"STAGED: {line.split()[0]}")

    def commit(self):
        with open(f"{MyVcs.vcs}/index", "r") as f:
            index_content = f.readlines()
        index_content = [line.strip() for line in index_content]
        print(index_content)

    def get_branch_latest_commit(self, branch):
        with open(f"{MyVcs.vcs}/refs/heads/{branch}", "r") as f:
            return f.read()
        
    def get_commit_id_from_curr_branch(self):
        curr_branch = self.get_current_branch()
        return self.get_branch_latest_commit(curr_branch)

    def update_latest_commit_in_curr_branch(self, commit_hash):
        branch = self.get_current_branch()
        with open(f"{MyVcs.vcs}/refs/heads/{branch}", "w") as f:
            return f.write(commit_hash)
        
    def make_commit(self):
        with open(f"{MyVcs.vcs}/index", "r") as f:
            index_content = f.readlines()
            if not index_content:
                print("Nothing to commit.")
                return
        index_content = [line.strip() for line in index_content]
        # process string to file name and blob hash
        index_content = [[line.split()[0], line.split()[1]] for line in index_content]
        tree, hashed_tree = self.create_tree(index_content)
        self.store_blob(tree, hashed_tree)

        latest_commit = self.get_commit_id_from_curr_branch()

        commit, hashed_commit = self.create_commit(hashed_tree, parent_commit=latest_commit)

        self.store_blob(commit, hashed_commit)

        # empty staging area
        with open(f"{MyVcs.vcs}/index", "w") as f:
            f.write("")

        # update latest commit in curr branch
        self.update_latest_commit_in_curr_branch(hashed_commit)

    def read_tree(self, m_hash):
        pass

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

    def read_hash(self, hash, callback, all_comm):

        # all_comm = []

        dir_path = os.path.join(MyVcs.vcs, "objects", hash[:2])
        blob_path = os.path.join(dir_path, hash[2:])

        with open(blob_path, "r") as f:
            content = f.read()
            content = content.split("\n")
            f.close()
        print(f.closed)
        
        
        
        for line in content:
            if "parent" in line:
                parent_commit = line.split(" ")[1]
                if parent_commit:
                    # all_comm.append(parent_commit)
                    callback(all_comm, parent_commit)
                    self.read_hash(parent_commit, callback, all_comm)

    def display_commit_tree(self):
        all_comm = []

        def collect_commits(all_comm, commit):
            all_comm.append(commit)
            return all_comm

        self.read_hash(self.get_commit_id_from_curr_branch(), collect_commits, all_comm)

        print(f"{self.get_commit_id_from_curr_branch()} <- HEAD")
        for commit in all_comm:
            print(commit)
    

# vcs = MyVcs()
# file_name = "to.txt"

# content = vcs.read_file(file_name)
# vcs.init()
# vcs.show_branches()
# blob_1, hashed_blob_1 = vcs.create_blob(file_name)
# vcs.store_blob(content, hashed_blob_1)
# tree, hashed_tree = vcs.create_tree(file_name, hashed_blob_1)
# vcs.store_blob(tree, hashed_tree)
# # hashed_tree = b'tree 34\x00100655 my.txt\x00Z\xb2\xf8\xa42:\xba\xfb\x10\xab\xb6\x86W\xd9\xd3\x9f\x1awPW'
# commit, hashed_commit = vcs.create_commit(hashed_tree)
# vcs.store_blob(commit, hashed_commit)
# vcs.stage_files(file_name)
# vcs.show_staged_files()
# vcs.commit()