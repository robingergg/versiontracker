from main import *
from main import _empty_detached_state
import cmd2
import shutil


vcs = MyVcs()

stage_parser = cmd2.Cmd2ArgumentParser()
stage_parser.add_argument('-f', '--files', nargs='+', help='Files to be staged')

show_modified_files_parser = cmd2.Cmd2ArgumentParser()
show_log_graph_parser = cmd2.Cmd2ArgumentParser()

commit_parser = cmd2.Cmd2ArgumentParser()
commit_parser.add_argument('-m', '--message')

show_staged_files_parser = cmd2.Cmd2ArgumentParser()
read_tree_parser = cmd2.Cmd2ArgumentParser()

ammend_parser = cmd2.Cmd2ArgumentParser()
ammend_parser.add_argument('-m', '--message')

difference_parser = cmd2.Cmd2ArgumentParser()
difference_parser.add_argument('-h1', '--hash-1')
difference_parser.add_argument('-h2', '--hash-2')
difference_parser.add_argument('-f', '--filenames', nargs='+')
difference_parser.add_argument('-s', '--staged', action="store_true")

show_file_difference_parser = cmd2.Cmd2ArgumentParser()
show_file_difference_parser.add_argument('-f', '--filenames')

reset_hard_parser = cmd2.Cmd2ArgumentParser()
reset_hard_parser.add_argument('-c', '--commit')

reset_soft_parser = cmd2.Cmd2ArgumentParser()
reset_soft_parser.add_argument('-c', '--commit')

interactive_rebase_parser = cmd2.Cmd2ArgumentParser()
interactive_rebase_parser.add_argument('-c', '--commit')

continue_rebase_parser = cmd2.Cmd2ArgumentParser()

restore_parser = cmd2.Cmd2ArgumentParser()
restore_parser.add_argument('-f', '--files')
restore_parser.add_argument('-s', '--staged', action="store_true")

untracked_parser = cmd2.Cmd2ArgumentParser()


class MainVcs(cmd2.Cmd):

    def do_init(self, args: cmd2.Statement):
        vcs.init()

    @cmd2.with_argparser(read_tree_parser)
    def do_read_tree(self):
        """Reads the tree of a given commit"""
        
    @cmd2.with_argparser(difference_parser)
    def do_difference(self, args):
        """
        Displays the difference between two files.
        """
        if args.hash_1 and args.hash_2:
            vcs.read_commit_differences(args.hash_1, args.hash_2, staged=args.staged)
        elif args.filenames:
            vcs.read_commit_differences(file_names=args.filenames, staged=args.staged)

    def do_remove_vcs(self, args):
        if os.path.exists(MyVcs.vcs):
            shutil.rmtree(MyVcs.vcs)
        else:
            print(f"There is no such path to remove: {MyVcs.vcs}")
        _empty_detached_state()

    @cmd2.with_argparser(stage_parser)
    def do_stage_files(self, args):
        """Stages the selected files"""
        files = args.files
        print(f"Files to stage: {files}")
        for f in files:
            vcs.stage_file(f)

    @cmd2.with_argparser(show_staged_files_parser)
    def do_show_staged(self, args):
        vcs.show_staged_files()

    @cmd2.with_argparser(commit_parser)
    def do_commit(self, args):
        msg = args.message if args.message else None 
        vcs.make_commit(message=msg)

    @cmd2.with_argparser(show_modified_files_parser)
    def do_show_modified_files(self, args):
        vcs.display_modified_files()

    @cmd2.with_argparser(show_log_graph_parser)
    def do_show_log_graph(self, args):
        vcs.display_commit_tree()

    @cmd2.with_argparser(ammend_parser)
    def do_ammend(self, args):
        message = None
        if args.message:
            message = args.message
        vcs.ammend(message)

    @cmd2.with_argparser(reset_hard_parser)
    def do_reset_hard(self, args):
        """
        Rebases to the selected commit.
        """
        self.poutput(args.commit)
        vcs.reset_hard(args.commit)

    @cmd2.with_argparser(reset_soft_parser)
    def do_reset_soft(self, args):
        """
        Rebases to the selected commit.
        """
        self.poutput(args.commit)
        vcs.reset_soft(args.commit)

    @cmd2.with_argparser(untracked_parser)
    def do_untracked_files(self, args):
        vcs.show_untracked_files()

    @cmd2.with_argparser(show_file_difference_parser)
    def do_show_file_difference(self, args):
        # file_names = [filename for filename in args.filenames]
        vcs.show_staged_difference(args.filenames)

    @cmd2.with_argparser(interactive_rebase_parser)
    def do_interactive_rebase(self, args):
        vcs.interactive_rebase(args.commit)

    @cmd2.with_argparser(continue_rebase_parser)
    def do_continue_rebase(self, args):
        vcs.continue_rebase()

    @cmd2.with_argparser(restore_parser)
    def do_restore(self, args):
        files = args.files.split(" ")
        vcs.restore(files, args.staged)

    def postloop(self):
        super().postloop()
        _empty_detached_state()


file_1 = "foo.txt"
file_2 = "foo_2.txt"


if __name__ == '__main__':
    import sys
    c = MainVcs()
    sys.exit(c.cmdloop())
