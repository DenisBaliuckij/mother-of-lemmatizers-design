"""Validate the self-describing `languages/` catalogue.

Each language lives in `languages/<glottocode>-<english-name>/` with four
files: `profile.yaml`, `en.md`, `ru.md` and `test-cases.tsv`. The conventions
are documented in `languages/README.md`. This tool checks that every language
directory follows them, so the catalogue stays machine-checkable, and that the
catalogue's `README.md` stays in step with the directories on disk.

Run it from the repository root:

    python scripts/validate_languages.py            # the real languages/ tree
    python scripts/validate_languages.py some/dir   # any catalogue root

It prints an `OK: <dir>` line per clean language and an `ERROR: <path>: <msg>`
line per problem, and exits non-zero if anything failed. The validation logic
lives in `validate_language()` and `check_readme()`, which take a directory and
return a list of error messages, so tests can call them directly on fixtures.

Standard library only, except for `pyyaml` to parse `profile.yaml`.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

# A language directory is `<glottocode>-<english-name>`; the glottocode is a
# Glottolog key: four lowercase letters followed by four digits (e.g. hung1274).
GLOTTOCODE_RE = re.compile(r"[a-z]{4}\d{4}")
FOLDER_RE = re.compile(r"(?P<glottocode>[a-z]{4}\d{4})-(?P<name>[a-z][a-z0-9-]*)")

REQUIRED_FILES = ("profile.yaml", "en.md", "ru.md", "test-cases.tsv")

TSV_COLUMNS = ("id", "form", "context", "lemma", "features", "requirements", "note")
TSV_HEADER = "\t".join(TSV_COLUMNS)

# A requirement ID such as HU-01: a 2–4 letter prefix and a 2+ digit number.
REQUIREMENT_ID_RE = re.compile(r"[A-Z]{2,4}-\d{2,}")
# Requirement IDs are defined as the first cell of a Markdown table row.
DEFINED_ID_RE = re.compile(r"^\|\s*([A-Z]{2,4}-\d{2,})\s*\|", re.MULTILINE)

# A Universal-Dependencies feature group: Key=Value, where Key may carry a
# layer such as Number[psor], and Value may list alternatives (Sing,Plur).
_FEATURE_GROUP = r"[A-Z][A-Za-z0-9]*(?:\[[a-z0-9]+\])?=[A-Za-z0-9]+(?:,[A-Za-z0-9]+)*"
FEATURES_RE = re.compile(rf"^{_FEATURE_GROUP}(?:\|{_FEATURE_GROUP})*$")

# A Markdown inline link: [text](target).
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# Link targets that point outside the filesystem; not checked for existence.
_EXTERNAL_LINK_RE = re.compile(r"^(?:https?|mailto|ftp):", re.IGNORECASE)


def iter_language_dirs(languages_root: Path) -> list[Path]:
    """Return the language directories under `languages_root`, sorted by name.

    A language directory is any immediate subdirectory that contains a
    `profile.yaml`; the folder that holds only `README.md` is thereby skipped.
    """
    languages_root = Path(languages_root)
    if not languages_root.is_dir():
        return []
    return sorted(
        child
        for child in languages_root.iterdir()
        if child.is_dir() and (child / "profile.yaml").is_file()
    )


def defined_ids(markdown: str) -> set[str]:
    """Requirement IDs defined in `markdown` (first cell of a table row)."""
    return set(DEFINED_ID_RE.findall(markdown))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _validate_profile(directory: Path, folder_glottocode: str | None) -> list[str]:
    path = directory / "profile.yaml"
    if not path.is_file():
        return []  # already reported as a missing file
    errors: list[str] = []
    try:
        data = yaml.safe_load(_read_text(path))
    except yaml.YAMLError as exc:
        detail = " ".join(str(exc).split())
        return [f"profile.yaml: invalid YAML: {detail}"]
    if not isinstance(data, dict):
        return ["profile.yaml: top level must be a mapping"]
    language = data.get("language")
    if not isinstance(language, dict):
        return ["profile.yaml: missing `language` mapping"]
    for key in ("name", "glottocode", "iso639_3"):
        value = language.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"profile.yaml: language.{key} is missing or empty")
    profile_glottocode = language.get("glottocode")
    if (
        folder_glottocode is not None
        and isinstance(profile_glottocode, str)
        and profile_glottocode != folder_glottocode
    ):
        errors.append(
            f"profile.yaml: language.glottocode {profile_glottocode!r} does not "
            f"match the folder glottocode {folder_glottocode!r}"
        )
    return errors


def _split_row(line: str) -> list[str] | None:
    """Split a TSV data row into its 7 fields, or None if the count is wrong.

    A trailing empty `note` field may be omitted, so a row with six fields is
    accepted and padded with an empty note (this is how the catalogue is kept).
    """
    fields = line.split("\t")
    if len(fields) == 7:
        return fields
    if len(fields) == 6:
        return fields + [""]
    return None


def _validate_test_cases(directory: Path) -> list[str]:
    path = directory / "test-cases.tsv"
    if not path.is_file():
        return []  # already reported as a missing file
    errors: list[str] = []
    lines = _read_text(path).splitlines()
    if not lines:
        return ["test-cases.tsv: file is empty"]
    if lines[0] != TSV_HEADER:
        errors.append(
            "test-cases.tsv: first line must be the exact header "
            f"{TSV_HEADER!r}"
        )
        # A wrong header means the columns cannot be trusted; stop here.
        return errors

    seen_ids: set[str] = set()
    for offset, line in enumerate(lines[1:], start=2):
        fields = _split_row(line)
        if fields is None:
            errors.append(
                f"test-cases.tsv line {offset}: has {line.count(chr(9)) + 1} "
                "tab-separated fields, expected 7 (6 is allowed when the trailing "
                "note is empty)"
            )
            continue
        id_, form, _context, lemma, features, requirements, _note = fields
        where = f"test-cases.tsv line {offset}"
        if not id_:
            errors.append(f"{where}: id is empty")
        elif id_ in seen_ids:
            errors.append(f"{where}: duplicate id {id_!r}")
        else:
            seen_ids.add(id_)
        if not form:
            errors.append(f"{where}: form is empty")
        if not lemma:
            errors.append(f"{where}: lemma is empty")
        if features and not FEATURES_RE.fullmatch(features):
            errors.append(
                f"{where}: features {features!r} are not UD-style Key=Value "
                "groups joined by '|'"
            )
        if requirements:
            for token in requirements.split(","):
                token = token.strip()
                if not REQUIREMENT_ID_RE.fullmatch(token):
                    errors.append(
                        f"{where}: requirement id {token!r} is not of the form "
                        "<PREFIX>-NN"
                    )
    return errors


def _referenced_requirement_ids(directory: Path) -> set[str]:
    path = directory / "test-cases.tsv"
    if not path.is_file():
        return set()
    referenced: set[str] = set()
    lines = _read_text(path).splitlines()
    if not lines or lines[0] != TSV_HEADER:
        return referenced
    for line in lines[1:]:
        fields = _split_row(line)
        if fields is None:
            continue
        requirements = fields[5]
        for token in requirements.split(","):
            token = token.strip()
            if REQUIREMENT_ID_RE.fullmatch(token):
                referenced.add(token)
    return referenced


def _validate_requirement_ids(directory: Path) -> list[str]:
    errors: list[str] = []
    en_path, ru_path = directory / "en.md", directory / "ru.md"
    en_ids = defined_ids(_read_text(en_path)) if en_path.is_file() else None
    ru_ids = defined_ids(_read_text(ru_path)) if ru_path.is_file() else None

    if en_ids is not None and ru_ids is not None and en_ids != ru_ids:
        only_en = ", ".join(sorted(en_ids - ru_ids))
        only_ru = ", ".join(sorted(ru_ids - en_ids))
        detail = []
        if only_en:
            detail.append(f"only in en.md: {only_en}")
        if only_ru:
            detail.append(f"only in ru.md: {only_ru}")
        errors.append(
            "requirement IDs defined in en.md and ru.md differ (" + "; ".join(detail) + ")"
        )

    defined = (en_ids or set()) | (ru_ids or set())
    for req_id in sorted(_referenced_requirement_ids(directory)):
        if req_id not in defined:
            errors.append(
                f"test-cases.tsv references requirement {req_id}, which is not "
                "defined in en.md or ru.md"
            )
    return errors


def validate_language(directory: Path | str) -> list[str]:
    """Validate one language directory; return a list of error messages.

    An empty list means the directory follows every catalogue convention.
    """
    directory = Path(directory)
    errors: list[str] = []

    match = FOLDER_RE.fullmatch(directory.name)
    folder_glottocode = match.group("glottocode") if match else None
    if match is None:
        errors.append(
            f"folder name {directory.name!r} is not '<glottocode>-<english-name>' "
            "(glottocode = four lowercase letters followed by four digits)"
        )

    for fname in REQUIRED_FILES:
        if not (directory / fname).is_file():
            errors.append(f"missing required file {fname}")

    errors += _validate_profile(directory, folder_glottocode)
    errors += _validate_test_cases(directory)
    errors += _validate_requirement_ids(directory)
    return errors


def check_readme(languages_root: Path | str) -> list[str]:
    """Check `languages_root/README.md` against the directories on disk.

    Every language directory must be linked from the README, and every local
    link target in the README must exist.
    """
    languages_root = Path(languages_root)
    readme = languages_root / "README.md"
    if not readme.is_file():
        return [f"{readme} not found"]

    errors: list[str] = []
    text = _read_text(readme)
    targets = [t.strip() for t in MD_LINK_RE.findall(text)]

    for target in targets:
        if _EXTERNAL_LINK_RE.match(target) or target.startswith("#"):
            continue
        local = target.split("#", 1)[0]
        if not local:
            continue
        if not (languages_root / local).exists():
            errors.append(f"README link target {target!r} does not exist")

    for directory in iter_language_dirs(languages_root):
        name = directory.name
        if not any(t == name or t.startswith(name + "/") for t in targets):
            errors.append(f"README has no row linking to language folder {name!r}")

    return errors


def _default_languages_root() -> Path:
    return Path(__file__).resolve().parent.parent / "languages"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the languages/ catalogue and its README."
    )
    parser.add_argument(
        "languages_root",
        nargs="?",
        default=None,
        help="catalogue root (defaults to the repository's languages/ directory)",
    )
    args = parser.parse_args(argv)

    root = Path(args.languages_root) if args.languages_root else _default_languages_root()
    if not root.is_dir():
        print(f"ERROR: {root}: not a directory")
        return 1

    total_errors = 0
    for directory in iter_language_dirs(root):
        errors = validate_language(directory)
        if errors:
            for message in errors:
                print(f"ERROR: {directory}: {message}")
            total_errors += len(errors)
        else:
            print(f"OK: {directory}")

    for message in check_readme(root):
        print(f"ERROR: {root / 'README.md'}: {message}")
        total_errors += 1

    if total_errors:
        print(f"\n{total_errors} error(s) found.")
        return 1
    print("\nAll language catalogues are valid.")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
