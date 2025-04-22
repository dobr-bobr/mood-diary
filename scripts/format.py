import subprocess
import sys


def main():
    args = ["black", ".", "--line-length", "79"]

    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])

    result = subprocess.run(args)
    sys.exit(result.returncode)
