from __future__ import annotations

import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def run_and_log(log_path: Path, command: list[str]) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    with log_path.open("w", encoding="utf-8") as handle:
        handle.write(f"$ {' '.join(command)}\n")
        handle.write(f"started_at={started}\n\n")
        handle.flush()
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="")
            handle.write(line)
        return_code = process.wait()
        finished = datetime.now(timezone.utc).isoformat()
        handle.write(f"\nfinished_at={finished}\nreturn_code={return_code}\n")
    return return_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a command and capture stdout/stderr to a log file.")
    parser.add_argument("log_path", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        raise SystemExit("No command provided.")
    raise SystemExit(run_and_log(args.log_path, args.command))


if __name__ == "__main__":
    main()
