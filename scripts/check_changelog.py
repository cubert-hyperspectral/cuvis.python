#!/usr/bin/env python3
"""Validate CHANGELOG.md against the conventions in CONTRIBUTING.md.

Without arguments the structure is checked.
With --tag the tag, the pyproject version and the newest release section must all agree.
With --extract the body of one release section is written to stdout, for the GitHub Release text.
"""

import argparse
import re
import sys
import tomllib
from pathlib import Path

SECTIONS = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")

UNRELEASED = re.compile(r"^## \[Unreleased\]$")
RELEASE = re.compile(r"^## \[(\d+(?:\.\d+)*(?:\.post\d+)?)\] - (\d{4}-\d{2}-\d{2})$")
SECTION = re.compile(r"^### (.+)$")
BULLET = re.compile(r"^- \S")
CONTINUATION = re.compile(r"^ {2}\S")


def version_key(version):
    """Order releases the way PEP 440 does, so 3.5.3 and 3.5.3.0 compare equal."""
    base, _, post = version.partition(".post")
    padded = (tuple(int(p) for p in base.split(".")) + (0,) * 8)[:8]
    return padded, int(post or 0)


def releases(lines):
    """Yield (line_number, version, date) for every release header."""
    return (
        (no, *match.groups())
        for no, line in enumerate(lines, 1)
        if (match := RELEASE.match(line))
    )


def section_errors(no, heading, seen):
    if heading not in SECTIONS:
        yield f"{no}: unknown section '{heading}', expected one of {', '.join(SECTIONS)}"
    elif heading in seen:
        yield f"{no}: section '{heading}' appears twice in the same release"
    elif seen and SECTIONS.index(heading) < max(SECTIONS.index(s) for s in seen):
        yield f"{no}: section '{heading}' is out of order, expected {' < '.join(SECTIONS)}"


def structure_errors(lines):
    """Report every convention violation, one message per offending line."""
    if not any(map(UNRELEASED.match, lines)):
        yield "0: no '## [Unreleased]' section; add one so the next change has a home"

    versions = [(no, v) for no, v, _ in releases(lines)]
    for (_, previous), (no, version) in zip(versions, versions[1:]):
        if version_key(version) == version_key(previous):
            yield f"{no}: version {version} duplicates {previous} (equal under PEP 440)"
        elif version_key(version) > version_key(previous):
            yield f"{no}: version {version} must sort below {previous}"

    seen = set()
    in_section = False
    for no, line in enumerate(lines, 1):
        if line.startswith("## "):
            if not (UNRELEASED.match(line) or RELEASE.match(line)):
                yield f"{no}: release header must be '## [<version>] - <YYYY-MM-DD>'"
            seen, in_section = set(), False
        elif match := SECTION.match(line):
            yield from section_errors(no, match.group(1), seen)
            if match.group(1) in SECTIONS:
                seen.add(match.group(1))
            in_section = True
        elif (
            in_section
            and line.strip()
            and not (BULLET.match(line) or CONTINUATION.match(line))
        ):
            yield f"{no}: expected a '- ' bullet or a two-space continuation line"


def body(lines, version):
    """The lines of one release section, without its header."""
    starts = [
        no for no, v, _ in releases(lines) if version_key(v) == version_key(version)
    ]
    if not starts:
        raise SystemExit(f"no release section for version {version} in CHANGELOG.md")
    rest = lines[starts[0] :]
    end = next(
        (i for i, line in enumerate(rest) if i and line.startswith("## ")), len(rest)
    )
    return "\n".join(rest[1:end]).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    parser.add_argument(
        "--tag", help="release tag (vX.Y.Z.W) that must match version and changelog"
    )
    parser.add_argument(
        "--extract", help="print the body of this release section and exit"
    )
    args = parser.parse_args()

    lines = args.changelog.read_text(encoding="utf-8").splitlines()

    if args.extract:
        print(body(lines, args.extract))
        return 0

    errors = list(structure_errors(lines))

    if args.tag:
        version = tomllib.loads(args.pyproject.read_text(encoding="utf-8"))["project"][
            "version"
        ]
        newest = next((v for _, v, _ in releases(lines)), None)
        if args.tag != f"v{version}":
            errors.append(
                f"0: tag {args.tag} does not match pyproject version {version}"
            )
        if newest != version:
            errors.append(
                f"0: newest changelog release is {newest}, expected {version}"
            )
        if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", version):
            errors.append(f"0: version {version} is not MAJOR.MINOR.PATCH.TWEAK")

    for error in errors:
        print(f"{args.changelog}:{error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
