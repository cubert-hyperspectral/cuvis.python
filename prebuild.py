import subprocess
from pathlib import Path


def get_git_commit_hash():
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .decode("ascii")
            .strip()
        )
    except subprocess.CalledProcessError:
        return "unknown"


with open(Path(__file__).parent / "git-hash.txt", "w") as f:
    f.write(f"{get_git_commit_hash()}\n")

print("git-hash.txt created.")
