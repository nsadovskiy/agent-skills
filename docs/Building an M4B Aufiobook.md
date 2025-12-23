# Building an M4B Audiobook from Audio Files on Linux

This document describes a complete, reproducible process for building a single **M4B** file from a set of audio files (MP3, M4A, M4B, AAC, FLAC, OGG, WAV, etc.), preserving the maximum amount of metadata, normalizing all text to UTF-8, and creating chapter markers with correct timestamps.

> **Important encoding assumption**
> Any non-Unicode (non-UTF-8) text encountered in filenames, tags, or auxiliary text files MUST be treated as **Russian text** and converted to UTF-8 accordingly (typically from CP1251 or KOI8-R).

---

## Goals

* Combine multiple audio files of various formats into a single M4B
* Correctly process source MP3, M4A, M4B, and other containers
* Merge a multi-part audiobook already split into several M4B files
* Preserve and transfer common metadata (author, title, album, etc.)
* Normalize Cyrillic text and filenames to UTF-8
* Automatically or semi-automatically generate chapters
* Produce a file correctly recognized by players as an audiobook

---

## Overall Pipeline

1. Prepare input files (ordering, filenames, encodings, formats)
2. Normalize heterogeneous formats to a single processing flow
3. Normalize tags and character encodings
4. Inspect durations and metadata
5. Generate chapters
6. Concatenate and encode into M4B
7. Write audiobook-specific metadata and cover art
8. Validate the result

---

## Command-Line Tools

### Coreutils

Used for file discovery, sorting, and list generation:

* `find`
* `sort -V`
* `xargs`
* `printf`

---

### convmv

**Purpose:** Convert filenames to UTF-8 (CP1251, KOI8-R, etc.). All non-Unicode names are assumed to be Russian.

```bash
convmv -f CP1251 -t UTF-8 --notest -r .
```

---

### mutagen / mid3iconv

**Purpose:** Normalize MP3 ID3 tags to Unicode (ID3v2). Non-Unicode tags are assumed to be Russian.

```bash
mid3iconv -e CP1251 *.mp3
```

---

### ffmpeg / ffprobe

**Purpose:**

* Universal processing of all common audio formats
* Decoding and re-encoding
* Concatenation of heterogeneous containers
* AAC / ALAC encoding
* Chapter import
* Transfer of basic metadata

Get file duration (any supported format):

```bash
ffprobe -v error -show_entries format=duration \
  -of default=nw=1:nk=1 "01.any"
```

---

### exiftool

**Purpose:** Universal metadata inspection and editing for MP3 and MP4/M4B, with explicit charset control.

Read tags:

```bash
exiftool -G1 -a -s "01.mp3"
```

Read ID3v1 assuming Russian CP1251:

```bash
exiftool -charset id3=cp1251 -G1 -a -s "01.mp3"
```

---

### AtomicParsley

**Purpose:** Write iTunes-compatible MP4 metadata (Audiobook media type, cover art).

```bash
AtomicParsley "book.m4b" \
  --title "Title" \
  --artist "Author" \
  --album "Book Title" \
  --albumArtist "Author" \
  --genre "Audiobook" \
  --stik "Audiobook" \
  --artwork cover.jpg \
  --overWrite
```

---

### mp4chaps (mp4v2)

**Purpose:** Export, import, and convert chapters (QuickTime / Nero styles).

Export chapters:

```bash
mp4chaps -x "book.m4b"
```

Import chapters as QuickTime:

```bash
mp4chaps -i -Q -z "book.m4b"
```

---

### MP4Box (gpac)

**Purpose:** Import chapters from text files and inspect MP4/M4B containers.

```bash
MP4Box -chap chapters.txt "book.m4b"
```

Example `chapters.txt`:

```
00:00:00.000 Chapter 1
00:12:34.500 Chapter 2
```

---

### Bento4 (mp4info, mp4dump)

**Purpose:** Low-level inspection of MP4/M4B container structure.

```bash
mp4info "book.m4b"
mp4dump --verbosity 1 "book.m4b" | less
```

---

## Typical Build Scenarios

### Scenario 0. Files Organized in Subdirectories (e.g., by Chapters)

Audiobooks are often stored in a hierarchical structure:

```
book/
├── 01_Introduction/
│   ├── 01.mp3
│   └── 02.mp3
├── 02_Chapter_1/
│   ├── 01.mp3
│   └── 02.mp3
└── 03_Chapter_2/
    └── 01.mp3
```

Playback order is determined by:

1. Directory order (lexicographic or numeric prefixes)
2. File order within each directory

Subdirectories usually correspond to top-level chapters.

#### 0.1. Generating a Global File List (Recursive)

```bash
find . -type f \
  \( -iname '*.mp3' -o -iname '*.m4a' -o -iname '*.aac' -o -iname '*.flac' -o -iname '*.ogg' -o -iname '*.wav' \) \
  -print0 \
| sort -zV \
| xargs -0 -I{} printf "file '%s'\n" "$PWD/{}" \
> files.txt
```

This works correctly if:

* directories use numeric or lexicographic prefixes;
* files inside directories are ordered by name.

#### 0.2. Generating Chapters from Directory Structure

Recommended strategy:

* **Chapter = directory**
* Chapter title is derived from the directory name
* Chapter start time equals the start of the first file in that directory

Algorithm:

1. Traverse files in playback order
2. Detect directory changes
3. On directory change, create a new chapter
4. Accumulate duration using `ffprobe`

This approach:

* faithfully restores book structure;
* does not depend on per-file ID3 titles;
* produces readable chapter names automatically.

The same algorithm is reused in Scenarios A and B.

---

### Scenario A. Heterogeneous Audio Files (MP3, M4A, FLAC, etc.) → One M4B

#### 1. Build an Ordered File List

```bash
find . -maxdepth 1 -type f \
  \( -iname '*.mp3' -o -iname '*.m4a' -o -iname '*.aac' -o -iname '*.flac' -o -iname '*.ogg' -o -iname '*.wav' \) \
  -print0 \
| sort -zV \
| xargs -0 -I{} printf "file '%s'\n" "$PWD/{}" \
> files.txt
```

---

#### 2. Generate Chapter Metadata (`meta.txt`)

FFmpeg metadata format:

```text
;FFMETADATA1
[CHAPTER]
TIMEBASE=1/1000
START=0
END=123456
title=Chapter 1
```

Generated via a script using bash + ffprobe + exiftool.

---

#### 3. Build the M4B File

```bash
ffmpeg -f concat -safe 0 -i files.txt \
  -f ffmetadata -i meta.txt \
  -c:a aac -b:a 96k \
  -map_metadata 1 -map_chapters 1 \
  -movflags +faststart \
  book.m4b
```

---

#### 4. Final Metadata Pass

```bash
AtomicParsley book.m4b \
  --stik Audiobook \
  --artwork cover.jpg \
  --overWrite
```

---

### Scenario B. Multi-Part Audiobook (Multiple M4B Files) → One M4B

Here, the source files are already MP4/M4B containers and may contain their own chapters and metadata.

#### Characteristics

* Audio can be concatenated **without re-encoding** if codecs match
* Chapters must be remapped into a single continuous timeline
* Global metadata is taken from the first file or defined manually

#### 1. List Source M4B Files

```bash
find . -maxdepth 1 -type f -iname '*.m4b' -print0 \
| sort -zV \
| xargs -0 -I{} printf "file '%s'\n" "$PWD/{}" \
> files.txt
```

#### 2. Extract and Merge Chapters

For each part:

```bash
mp4chaps -x part01.m4b
```

Chapter timestamps are shifted by cumulative duration and merged into a single `chapters.txt`.

#### 3. Concatenate Without Re-encoding

```bash
ffmpeg -f concat -safe 0 -i files.txt \
  -c copy \
  -movflags +faststart \
  book.m4b
```

#### 4. Import Combined Chapters

```bash
mp4chaps -i -Q -z book.m4b
```

---

## Validation

* `mediainfo book.m4b`
* `mp4info book.m4b`
* Verify chapters in target players (Apple Books, Smart AudioBook Player, VLC)

---

## Recommendations

* Prefer QuickTime-style chapters for maximum compatibility
* Derive chapter titles from ID3 `Title`, directory names, or filenames
* Treat all non-Unicode text as Russian and convert to UTF-8 early
* Keep all intermediate text files strictly UTF-8
* Automate the pipeline using a Makefile or shell script

---

## Summary

The described set of CLI tools fully covers the entire lifecycle of building an M4B audiobook on Linux — from poorly encoded, heterogeneous source files to a clean, player-compatible result with chapters and rich metadata.
