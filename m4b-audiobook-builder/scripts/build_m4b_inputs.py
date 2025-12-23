#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

DEFAULT_EXTENSIONS = {
    ".mp3",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
    ".wav",
    ".m4b",
}


def natural_key(text: str) -> List[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", text)]


def collect_files(root: Path, recursive: bool, extensions: set[str]) -> List[Path]:
    if recursive:
        candidates = [p for p in root.rglob("*") if p.is_file()]
    else:
        candidates = [p for p in root.iterdir() if p.is_file()]

    files = [p for p in candidates if p.suffix.lower() in extensions]
    files.sort(key=lambda p: natural_key(str(p.relative_to(root))))
    return files


def write_concat_list(files: Iterable[Path], output_path: Path) -> None:
    for path in files:
        if "'" in str(path):
            raise ValueError(f"file path contains a single quote: {path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for path in files:
            handle.write(f"file '{path.resolve()}'\n")


def probe_duration_ms(path: Path) -> int:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    seconds = float(result.stdout.strip())
    return int(round(seconds * 1000))


def chapter_title_from_dir(path: Path, root: Path) -> str:
    relative = path.parent.relative_to(root)
    if str(relative) == ".":
        return root.name or "Root"
    return relative.as_posix()


def build_chapters(
    files: List[Path],
    root: Path,
    chapter_mode: str,
) -> List[tuple[int, int, str]]:
    if chapter_mode == "none":
        return []

    durations_ms = [probe_duration_ms(path) for path in files]

    if chapter_mode == "file":
        chapters: List[tuple[int, int, str]] = []
        start_ms = 0
        for path, duration_ms in zip(files, durations_ms):
            end_ms = start_ms + duration_ms
            chapters.append((start_ms, end_ms, path.stem))
            start_ms = end_ms
        return chapters

    chapters = []
    chapter_starts: List[int] = []
    chapter_titles: List[str] = []
    current_key = None
    cumulative_ms = 0

    for path, duration_ms in zip(files, durations_ms):
        dir_title = chapter_title_from_dir(path, root)
        if dir_title != current_key:
            chapter_titles.append(dir_title)
            chapter_starts.append(cumulative_ms)
            current_key = dir_title
        cumulative_ms += duration_ms

    total_ms = cumulative_ms
    for index, title in enumerate(chapter_titles):
        start_ms = chapter_starts[index]
        end_ms = chapter_starts[index + 1] if index + 1 < len(chapter_starts) else total_ms
        chapters.append((start_ms, end_ms, title))

    return chapters


def write_ffmetadata(chapters: List[tuple[int, int, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write(";FFMETADATA1\n")
        for start_ms, end_ms, title in chapters:
            handle.write("[CHAPTER]\n")
            handle.write("TIMEBASE=1/1000\n")
            handle.write(f"START={start_ms}\n")
            handle.write(f"END={end_ms}\n")
            handle.write(f"title={title}\n")


def parse_extensions(value: str) -> set[str]:
    extensions = set()
    for item in value.split(","):
        item = item.strip().lower()
        if not item:
            continue
        if not item.startswith("."):
            item = f".{item}"
        extensions.add(item)
    return extensions


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate ffmpeg concat and chapter metadata files for M4B builds.",
    )
    parser.add_argument("--root", default=".", help="Root directory containing audio files.")
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan subdirectories and keep natural order.",
    )
    parser.add_argument(
        "--chapter-mode",
        choices=["dir", "file", "none"],
        default="dir",
        help="Create chapters per directory, per file, or not at all.",
    )
    parser.add_argument(
        "--extensions",
        default=",".join(sorted(ext.lstrip(".") for ext in DEFAULT_EXTENSIONS)),
        help="Comma-separated extensions to include.",
    )
    parser.add_argument("--files-out", default="files.txt", help="Concat list output file.")
    parser.add_argument("--meta-out", default="meta.txt", help="FFMETADATA output file.")

    args = parser.parse_args()
    root = Path(args.root).resolve()
    extensions = parse_extensions(args.extensions)

    files = collect_files(root, args.recursive, extensions)
    if not files:
        print("No matching audio files found.", file=sys.stderr)
        return 2

    try:
        write_concat_list(files, Path(args.files_out))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 3

    if args.chapter_mode == "none":
        return 0

    try:
        chapters = build_chapters(files, root, args.chapter_mode)
    except subprocess.CalledProcessError as exc:
        print("ffprobe failed; ensure ffmpeg/ffprobe are installed.", file=sys.stderr)
        print(exc.stderr, file=sys.stderr)
        return 4

    write_ffmetadata(chapters, Path(args.meta_out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
