import os
import sys
import argparse
import datetime
import contextlib
from fvs.repo import FVSRepo
from fvs.exceptions import FVSNothingToCommit, FVSEmptyCommitMessage, FVSStateNotFound, FVSNothingToRestore

version = 'FVS 0.2'


def fvs_cli():
    parser = argparse.ArgumentParser(description='FVS')
    parser.add_argument('-v', '--version', action='version', version=version)

    subparsers = parser.add_subparsers(dest='command', help='sub-command help')

    init_parser = subparsers.add_parser("init", help="Create a new FVS repository")
    init_parser.add_argument('-i', '--ignore', help='patterns to ignore', action='append', default=[], required=False)
    init_parser.add_argument('-p', '--path', help='path to the repository', default=os.getcwd())
    init_parser.add_argument('-c', '--use-compression', help='use compression', action='store_true', default=False)

    commit_parser = subparsers.add_parser("commit", help="Commit changes to the repository")
    commit_parser.add_argument('-i', '--ignore', help='patterns to ignore', action='append', default=[], required=False)
    commit_parser.add_argument('-m', '--message', help='commit message', nargs='+', required=True)

    states_parser = subparsers.add_parser("states", help="List all states in the repository")

    restore_parser = subparsers.add_parser("restore", help="Restore a state from the repository")
    restore_parser.add_argument('-i', '--ignore', help='patterns to ignore', action='append', default=[], required=False)
    restore_parser.add_argument('-s', '--state-id', help='state id', required=True)

    args = parser.parse_args()

    if args.command == 'init':
        repo = FVSRepo(args.path, args.use_compression)

        with contextlib.suppress(FVSNothingToCommit):
            repo.commit("Init", args.ignore)

        sys.stdout.write("Initialized FVS repository in {}\n".format(args.path))
        sys.exit(0)

    elif args.command == 'commit':
        repo = FVSRepo(os.getcwd())
        message = ' '.join(args.message)

        try:
            sys.stdout.write("Committing...\n")
            res = repo.commit(message, args.ignore)
            sep = "-" * 10
            sys.stdout.write("\nCommitted state {}\nMessage: {}\nDate: {}\n{}\nAdded files: {}\nRemoved files: {}\nModified files: {}\nIntact files: {}\n".format(
                res['state_id'],
                res['message'],
                datetime.datetime.fromtimestamp(res['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                sep,
                res["added"],
                res["removed"],
                res["modified"],
                res["intact"]
            ))
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
            sym = "\033[32m➔" if k == repo.active_state_id else "-"
            sys.stdout.write(
                "{} ({}): {}\n\t{}\n\n\033[0m".format(
                    sym, k, v["message"], datetime.datetime.fromtimestamp(v["timestamp"]))
            )

        sys.exit(0)

    elif args.command == 'restore':
        repo = FVSRepo(os.getcwd())
        try:
            repo.restore_state(args.state_id, args.ignore)
            sys.stdout.write("Restored state\n")
            sys.exit(0)
        except FVSStateNotFound:
            sys.stderr.write("State {} not found\n".format(args.state_id))
            sys.exit(1)
        except FVSNothingToRestore:
            sys.stderr.write("Nothing to restore from state {}\n".format(args.state_id))
            sys.exit(1)

    elif args.command == 'active':
        repo = FVSRepo(os.getcwd())
        if repo.active_state_id in [-1, None]:
            sys.stdout.write("No active state\n")
            sys.exit(0)
        sys.stdout.write("Active state is {}\n".format(repo.active_state_id))
        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    fvs_cli()
    sys.exit(0)
