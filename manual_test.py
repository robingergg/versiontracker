from main import *
import cmd2


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

class MainVcs(cmd2.Cmd):

    def do_init(self, args: cmd2.Statement):
        vcs.init()

    @cmd2.with_argparser(read_tree_parser)
    def do_read_tree(self):
        """Reads the tree of a given commit"""
        


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


file_1 = "my.txt"
file_2 = "to.txt"


if __name__ == '__main__':
    import sys
    c = MainVcs()
    sys.exit(c.cmdloop())
