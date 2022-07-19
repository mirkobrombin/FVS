import os
import sys
import argparse
import contextlib
from fvs.repo import FVSRepo
from fvs.exceptions import FVSNothingToCommit, FVSEmptyCommitMessage, FVSStateNotFound, FVSNothingToRestore

version = 'FVS 0.1'


def fvs_cli():
    parser = argparse.ArgumentParser(description='FVS')
    parser.add_argument('-v', '--version', action='version', version=version)
    parser.add_argument('command', help='command to run', default='help', nargs='?')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='arguments for the command', default=[])
    args = parser.parse_args()

    if args.command == 'help':
        parser.print_help()
        sys.exit(0)

    elif args.command == 'version':
        sys.stdout.write(version + '\n')
        sys.exit(0)

    elif args.command == 'init':
        path = os.getcwd() if len(args.args) == 0 else args.args[0]
        repo = FVSRepo(path)

        with contextlib.suppress(FVSNothingToCommit):
            repo.commit("Init")

        sys.stdout.write("Initialized FVS repository in {}\n".format(path))
        sys.exit(0)

    elif args.command == 'commit':
        if len(args.args) == 0:
            sys.stderr.write("No commit message provided\n")
            sys.exit(1)

        repo = FVSRepo(os.getcwd())

        try:
            sys.stdout.write("Committing...\n")
            repo.commit(args.args[0])
            sys.stdout.write("Committed state {}\n".format(repo.active_state_id))
            sys.exit(0)
        except FVSNothingToCommit:
            sys.stderr.write("Nothing to commit\n")
            sys.exit(1)
        except FVSEmptyCommitMessage:
            sys.stderr.write("Empty commit message\n")
            sys.exit(1)

    elif args.command == 'states':
        repo = FVSRepo(os.getcwd())

        if len(repo.states) == 0:
            sys.stdout.write("No states\n")
            sys.exit(0)

        for k, v in repo.states.items():
            sym = "➔" if k == repo.active_state_id else " "
            sys.stdout.write("- {} {} {}\n".format(sym, k, v))

        sys.exit(0)

    elif args.command == 'restore':
        if len(args.args) == 0:
            sys.stderr.write("No state id provided\n")
            sys.exit(1)

        state_id = args.args[0]

        repo = FVSRepo(os.getcwd())
        try:
            repo.restore_state(state_id)
            sys.stdout.write("Restored state\n")
            sys.exit(0)
        except FVSStateNotFound:
            sys.stderr.write("State {} not found\n".format(state_id))
            sys.exit(1)
        except FVSNothingToRestore:
            sys.stderr.write("Nothing to restore from state {}\n".format(state_id))
            sys.exit(1)

    elif args.command == 'active':
        repo = FVSRepo(os.getcwd())
        if repo.active_state_id in [-1, None]:
            sys.stdout.write("No active state\n")
            sys.exit(0)
        sys.stdout.write("Active state is {}\n".format(repo.active_state_id))
        sys.exit(0)

    else:
        sys.stderr.write("Unknown command: {}\n".format(args.command))
        sys.exit(1)


if __name__ == '__main__':
    fvs_cli()
    sys.exit(0)
