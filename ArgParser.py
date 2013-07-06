import argparse

class BetterFileArgParser(argparse.ArgumentParser):
    def convert_arg_line_to_args(self, arg_line):
        if not arg_line.startswith('#'):
            for arg in arg_line.split():
                yield arg