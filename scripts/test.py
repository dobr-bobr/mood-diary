import subprocess
import sys


def main():
    command = ["poetry", "run", "pytest"]
    test_path = ["./tests/"]
    args = []

    if len(sys.argv) > 1:
        if "-c" in sys.argv:
            args.append("--cov=mood_diary")
            if "-h" in sys.argv:
                args.append("--cov-report=html")

    result = subprocess.run(command + args + test_path)
    sys.exit(result.returncode)
