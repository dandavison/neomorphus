import os
import subprocess
import sys

from neomorphus import git


def _claude_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    return env


def invoke_claude(prompt: str) -> int:
    proc = subprocess.Popen(
        ["claude", "--print", "--output-format", "text", "-p", prompt],
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        env=_claude_env(),
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
    proc.wait()
    return proc.returncode


def run(prompt: str) -> None:
    if not git.is_clean():
        print("error: working tree is not clean; commit or stash changes first", file=sys.stderr)
        raise SystemExit(1)

    before = git.head_sha()
    returncode = invoke_claude(prompt)

    if returncode != 0:
        print(f"error: claude exited with code {returncode}", file=sys.stderr)
        raise SystemExit(returncode)

    if git.has_changes():
        first_line = prompt.split("\n")[0][:72]
        sha = git.commit_all(f"neo: {first_line}")
        print(f"\ncommitted: {before[:8]} -> {sha[:8]}")
    else:
        print(f"\nno changes (HEAD still {before[:8]})")
