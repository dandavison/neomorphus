import json
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


def _print_stream(line: str) -> None:
    """Parse a stream-json line and print human-readable output."""
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return
    msg_type = msg.get("type")
    if msg_type == "assistant":
        for block in msg.get("message", {}).get("content", []):
            if block.get("type") == "text":
                sys.stdout.write(block["text"])
                sys.stdout.write("\n")
                sys.stdout.flush()
            elif block.get("type") == "tool_use":
                name = block.get("name", "?")
                inp = block.get("input", {})
                if name == "Write":
                    sys.stdout.write(f"  write {inp.get('file_path', '')}\n")
                elif name == "Edit":
                    sys.stdout.write(f"  edit {inp.get('file_path', '')}\n")
                elif name == "Read":
                    sys.stdout.write(f"  read {inp.get('file_path', '')}\n")
                elif name == "Bash":
                    cmd = inp.get("command", "")
                    sys.stdout.write(f"  $ {cmd[:120]}\n")
                else:
                    sys.stdout.write(f"  [{name}]\n")
                sys.stdout.flush()
    elif msg_type == "result":
        result = msg.get("result", "")
        if result:
            sys.stdout.write(result)
            if not result.endswith("\n"):
                sys.stdout.write("\n")
            sys.stdout.flush()


def invoke_claude(prompt: str, *, interactive: bool = False) -> int:
    cmd = _claude_cmd()
    env = _claude_env()
    if interactive:
        os.execvpe(cmd, [cmd, prompt], env)
        return 0  # unreachable, satisfies type checker

    proc = subprocess.Popen(
        [cmd, "--print", "--verbose", "--output-format", "stream-json", "-p", prompt],
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        env=env,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        _print_stream(line)
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
