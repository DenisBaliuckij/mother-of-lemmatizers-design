"""Tests for the languages/ catalogue validator.

Each validation rule gets a passing case and at least one failing case, built
as tiny language directories under pytest's tmp_path. The real Hungarian
catalogue is exercised too, and must validate with zero errors.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from validate_languages import (
    REQUIRED_FILES,
    check_readme,
    defined_ids,
    iter_language_dirs,
    main,
    validate_language,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
REAL_LANGUAGES = REPO_ROOT / "languages"

VALID_PROFILE = """language:
  name: Testish
  glottocode: test1234
  iso639_3: tst

exception_tables:
  foo: []
"""

VALID_EN = """# Lemmatizer requirements: Testish

| ID | Requirement | Example | Component |
|---|---|---|---|
| TS-01 | First requirement | ex | rules |
| TS-02 | Second requirement | ex | rules |
"""

VALID_RU = """# Требования: Testish

| ID | Требование | Пример | Компонент |
|---|---|---|---|
| TS-01 | Первое требование | ex | правила |
| TS-02 | Второе требование | ex | правила |
"""

HEADER = "id\tform\tcontext\tlemma\tfeatures\trequirements\tnote"


def _row(
    id_: str = "ts-001",
    form: str = "forma",
    context: str = "",
    lemma: str = "lemma",
    features: str = "Case=Nom|Number=Sing",
    requirements: str = "TS-01,TS-02",
    note: str = "a note",
) -> str:
    return "\t".join([id_, form, context, lemma, features, requirements, note])


VALID_TSV = HEADER + "\n" + _row() + "\n"


def make_lang(
    root: Path,
    name: str = "test1234-testish",
    *,
    profile: str | None = VALID_PROFILE,
    en: str | None = VALID_EN,
    ru: str | None = VALID_RU,
    tsv: str | None = VALID_TSV,
) -> Path:
    """Create a language directory; pass a file's content as None to omit it."""
    directory = root / name
    directory.mkdir(parents=True, exist_ok=True)
    contents = {
        "profile.yaml": profile,
        "en.md": en,
        "ru.md": ru,
        "test-cases.tsv": tsv,
    }
    for fname, text in contents.items():
        if text is not None:
            (directory / fname).write_text(text, encoding="utf-8")
    return directory


# --- Rule: a valid directory passes -----------------------------------------


def test_valid_language_has_no_errors(tmp_path: Path) -> None:
    assert validate_language(make_lang(tmp_path)) == []


# --- Rule 1: folder name -----------------------------------------------------


def test_folder_name_without_glottocode_fails(tmp_path: Path) -> None:
    errors = validate_language(make_lang(tmp_path, name="testish"))
    assert any("folder name" in e for e in errors)


def test_folder_name_bad_glottocode_fails(tmp_path: Path) -> None:
    # Glottocode must be four lowercase letters + four digits.
    errors = validate_language(make_lang(tmp_path, name="Test1234-testish"))
    assert any("folder name" in e for e in errors)


# --- Rule 2: the four required files -----------------------------------------


def test_missing_file_fails(tmp_path: Path) -> None:
    errors = validate_language(make_lang(tmp_path, en=None))
    assert any("en.md" in e and "missing" in e for e in errors)


def test_required_files_constant() -> None:
    assert set(REQUIRED_FILES) == {"profile.yaml", "en.md", "ru.md", "test-cases.tsv"}


# --- Rule 3: profile.yaml ----------------------------------------------------


def test_profile_invalid_yaml_fails(tmp_path: Path) -> None:
    errors = validate_language(make_lang(tmp_path, profile="language: [unterminated\n"))
    assert any("profile.yaml" in e for e in errors)


def test_profile_missing_key_fails(tmp_path: Path) -> None:
    profile = "language:\n  name: Testish\n  glottocode: test1234\n"
    errors = validate_language(make_lang(tmp_path, profile=profile))
    assert any("iso639_3" in e for e in errors)


def test_profile_glottocode_must_match_folder(tmp_path: Path) -> None:
    profile = VALID_PROFILE.replace("test1234", "zzzz9999")
    errors = validate_language(make_lang(tmp_path, profile=profile))
    assert any("glottocode" in e for e in errors)


# --- Rule 4: test-cases.tsv --------------------------------------------------


def test_tsv_bad_header_fails(tmp_path: Path) -> None:
    bad = "id\tform\tlemma\n" + _row()
    errors = validate_language(make_lang(tmp_path, tsv=bad))
    assert any("header" in e for e in errors)


def test_tsv_wrong_field_count_fails(tmp_path: Path) -> None:
    short = HEADER + "\n" + "ts-001\tforma\tlemma\n"
    errors = validate_language(make_lang(tmp_path, tsv=short))
    assert any("field" in e for e in errors)


def test_tsv_duplicate_id_fails(tmp_path: Path) -> None:
    tsv = HEADER + "\n" + _row(id_="ts-001") + "\n" + _row(id_="ts-001") + "\n"
    errors = validate_language(make_lang(tmp_path, tsv=tsv))
    assert any("duplicate" in e.lower() for e in errors)


def test_tsv_empty_id_fails(tmp_path: Path) -> None:
    tsv = HEADER + "\n" + _row(id_="") + "\n"
    errors = validate_language(make_lang(tmp_path, tsv=tsv))
    assert any("id" in e.lower() for e in errors)


def test_tsv_empty_form_fails(tmp_path: Path) -> None:
    tsv = HEADER + "\n" + _row(form="") + "\n"
    errors = validate_language(make_lang(tmp_path, tsv=tsv))
    assert any("form" in e for e in errors)


def test_tsv_empty_lemma_fails(tmp_path: Path) -> None:
    tsv = HEADER + "\n" + _row(lemma="") + "\n"
    errors = validate_language(make_lang(tmp_path, tsv=tsv))
    assert any("lemma" in e for e in errors)


def test_tsv_bad_features_shape_fails(tmp_path: Path) -> None:
    tsv = HEADER + "\n" + _row(features="Case Nom; Number plural") + "\n"
    errors = validate_language(make_lang(tmp_path, tsv=tsv))
    assert any("features" in e for e in errors)


def test_tsv_layered_feature_key_allowed(tmp_path: Path) -> None:
    tsv = HEADER + "\n" + _row(features="Number[psor]=Plur|Person[psor]=1") + "\n"
    assert validate_language(make_lang(tmp_path, tsv=tsv)) == []


def test_tsv_empty_features_allowed(tmp_path: Path) -> None:
    tsv = HEADER + "\n" + _row(features="", requirements="TS-01") + "\n"
    assert validate_language(make_lang(tmp_path, tsv=tsv)) == []


def test_tsv_bad_requirement_id_shape_fails(tmp_path: Path) -> None:
    tsv = HEADER + "\n" + _row(requirements="TS-01, nonsense") + "\n"
    errors = validate_language(make_lang(tmp_path, tsv=tsv))
    assert any("requirement" in e.lower() for e in errors)


# --- Rule 5: requirement-ID consistency --------------------------------------


def test_en_ru_id_sets_must_match(tmp_path: Path) -> None:
    en = VALID_EN + "| TS-03 | Extra | ex | rules |\n"
    errors = validate_language(make_lang(tmp_path, en=en))
    assert any("TS-03" in e for e in errors)


def test_referenced_id_must_be_defined(tmp_path: Path) -> None:
    tsv = HEADER + "\n" + _row(requirements="TS-99") + "\n"
    errors = validate_language(make_lang(tmp_path, tsv=tsv))
    assert any("TS-99" in e for e in errors)


def test_defined_ids_reads_table_row_labels() -> None:
    text = "| TS-01 | x |\nTS-02 mentioned inline only\n| TS-03 | y |\n"
    assert defined_ids(text) == {"TS-01", "TS-03"}


# --- Rule 6: README cross-check ----------------------------------------------


def _readme_body(link_dir: str = "test1234-testish") -> str:
    return (
        "# Languages\n\n"
        "| Language | Links |\n"
        "|---|---|\n"
        f"| Testish | [ru]({link_dir}/ru.md) · [en]({link_dir}/en.md) |\n"
    )


def test_check_readme_passes(tmp_path: Path) -> None:
    make_lang(tmp_path)
    (tmp_path / "README.md").write_text(_readme_body(), encoding="utf-8")
    assert check_readme(tmp_path) == []


def test_check_readme_missing_row_fails(tmp_path: Path) -> None:
    make_lang(tmp_path)
    (tmp_path / "README.md").write_text("# Languages\n\nNothing here.\n", encoding="utf-8")
    errors = check_readme(tmp_path)
    assert any("test1234-testish" in e for e in errors)


def test_check_readme_broken_link_fails(tmp_path: Path) -> None:
    make_lang(tmp_path)
    body = _readme_body() + "\nSee [gone](test1234-testish/missing.md).\n"
    (tmp_path / "README.md").write_text(body, encoding="utf-8")
    errors = check_readme(tmp_path)
    assert any("missing.md" in e for e in errors)


# --- The real catalogue ------------------------------------------------------


def test_real_hungarian_passes() -> None:
    directory = REAL_LANGUAGES / "hung1274-hungarian"
    assert validate_language(directory) == []


def test_real_readme_passes() -> None:
    assert check_readme(REAL_LANGUAGES) == []


def test_iter_language_dirs_finds_hungarian() -> None:
    names = [d.name for d in iter_language_dirs(REAL_LANGUAGES)]
    assert "hung1274-hungarian" in names


# --- main() ------------------------------------------------------------------


def test_main_returns_zero_on_valid_tree(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    make_lang(tmp_path)
    (tmp_path / "README.md").write_text(_readme_body(), encoding="utf-8")
    assert main([str(tmp_path)]) == 0
    assert "OK" in capsys.readouterr().out


def test_main_returns_nonzero_on_invalid_tree(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    make_lang(tmp_path, en=None)
    (tmp_path / "README.md").write_text(_readme_body(), encoding="utf-8")
    assert main([str(tmp_path)]) == 1
    assert "ERROR" in capsys.readouterr().out


def test_main_on_real_tree_returns_zero() -> None:
    assert main([str(REAL_LANGUAGES)]) == 0
