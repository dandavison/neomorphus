import os
import subprocess
import sys

from neomorphus import git


def _claude_cmd() -> str:
    return os.environ.get("NEO_CLAUDE_CMD", "claude")


def _claude_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    return env


def invoke_claude(prompt: str, *, interactive: bool = False) -> int:
    cmd = _claude_cmd()
    env = _claude_env()
    if interactive:
        os.execvpe(cmd, [cmd, prompt], env)
        return 0  # unreachable, satisfies type checker

    proc = subprocess.Popen(
        [cmd, "--print", "--output-format", "text", "-p", prompt],
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        env=env,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
    proc.wait()
    return proc.returncode


def run(prompt: str, *, interactive: bool = False) -> None:
    if not git.is_clean():
        print("error: working tree is not clean; commit or stash changes first", file=sys.stderr)
        raise SystemExit(1)

    if interactive:
        invoke_claude(prompt, interactive=True)  # exec, does not return
        return  # unreachable

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
