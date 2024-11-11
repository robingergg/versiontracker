from main import *

vcs = MyVcs()




file_1 = "my.txt"
file_2 = "to.txt"
vcs.init()
# blob_1, hashed_blob_1 = vcs.create_blob(file_1)
# blob_2, hashed_blob_2 = vcs.create_blob(file_2)

# vcs.store_blob(blob_1, hashed_blob_1)
# vcs.store_blob(blob_2, hashed_blob_2)

# files = [[file_1, hashed_blob_1]]
# files = [[file_1, hashed_blob_1], [file_2, hashed_blob_2]]

# tree, hashed_tree = vcs.create_tree(files)
# vcs.store_blob(tree, hashed_tree)

# commit, hashed_commit = vcs.create_commit(hashed_tree)
# vcs.store_blob(commit, hashed_commit)

vcs.stage_files(file_1)
vcs.show_changed_objects("cd/1837365fe768e6d3a7659316ecd8f38cc4a58e")
# vcs.get_all_files_in_repo()
# vcs.make_commit()

# vcs.show_vcs_tree()