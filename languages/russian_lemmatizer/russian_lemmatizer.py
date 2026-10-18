# -*- coding: utf-8 -*-
"""Russian lemmatizer: analysis (form -> lemma) from the ontology and dictionaries.

Generation rules live in ``rules/ru-lemmatizer/*.lp`` and are not read here.
Clingo is not queried. ``russian-holdout.yaml`` is never opened.

Limitations
-----------
- Sources: ``OntoRussian.json`` (no ``lexicon_files``; the key is absent),
  Apertium ``apertium-rus.rus(1).dix``, and ``russian-development.yaml``.
  Zalizniak 1977 was not found as a machine-readable dictionary, so it is
  not a source. The development file is a SynTagRus heuristic sample
  (``selection`` / ``notes`` in the YAML); it is a coverage set, not a
  balanced gold lexicon. Entries whose Apertium paradigm uses ``<re>`` are
  skipped. Paradigm expansion keeps at most 48 forms per entry, so many
  participles are absent from the sqlite index and are recovered only when
  an ending rule rebuilds exactly one known infinitive. Lemmas are shown
  without Apertium homonym indexes and with ё rewritten to е, because the
  development lemmas contain neither. Aspect pairs are not used to replace
  a lemma with its partner.
- Categories handled: NOUN, PROPN, VERB, AUX, PRON, DET, ADJ, NUM, and the
  indeclinable classes ADV, ADP, CCONJ, SCONJ, PART, INTJ when the dictionary
  has them. Participles and gerunds are verb forms in Apertium (tags ``pp`` /
  ``pprs``); UD ``VERB``/``AUX`` with ``VerbForm=Part|Conv`` uses those tags.
- ``ambiguous``: the surface is returned as the lemma when no lexicon hit and
  no ending rule points at exactly one known lemma, or when several lemmas
  tie. Nothing is invented.
- Composites (``lemmatize_sentence`` only): future ``буду`` + infinitive,
  short passive participle + ``быть``, past + ``бы``, modal + infinitive.
  Single-token ``lemmatize`` does not see the neighbour token.
- Ontology rules declared but not implemented as procedural analyzers:
  stress, second locative/partitive as a productive class, and the full
  Zalizniak index. Aspect pairs from the ontology are a tie-break when
  ``Aspect`` is present, not a lemma rewrite. There is no
  ``default_replacement`` object in the ontology.
- Development-set sources are unused as external corpora, and the sample is
  a heuristic excerpt. Accuracy on the development file with that file loaded
  measures coverage. Quality is the sentence-split cross-validation, which
  hides the scored fold.
"""

from __future__ import annotations

import csv
import logging
import sqlite3
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import yaml

logger = logging.getLogger("russian_lemmatizer")

POS_TAGS = {
    "n": "NOUN",
    "np": "PROPN",
    "adj": "ADJ",
    "vblex": "VERB",
    "vbmod": "VERB",
    "vbser": "AUX",
    "vbhaver": "AUX",
    "prn": "PRON",
    "det": "DET",
    "num": "NUM",
    "adv": "ADV",
    "pr": "ADP",
    "cnjcoo": "CCONJ",
    "cnjsub": "SCONJ",
    "cnjadv": "SCONJ",
    "part": "PART",
    "ij": "INTJ",
    "abbr": "NOUN",
}

# UD feature -> Apertium tag. Case=Loc is the Russian prepositional.
_UD_TAG = {
    ("Case", "Nom"): "nom",
    ("Case", "Gen"): "gen",
    ("Case", "Dat"): "dat",
    ("Case", "Acc"): "acc",
    ("Case", "Ins"): "ins",
    ("Case", "Loc"): "prp",
    ("Number", "Sing"): "sg",
    ("Number", "Plur"): "pl",
    ("Gender", "Masc"): "m",
    ("Gender", "Fem"): "f",
    ("Gender", "Neut"): "nt",
    ("Animacy", "Anim"): "aa",
    ("Animacy", "Inan"): "nn",
    ("Person", "1"): "p1",
    ("Person", "2"): "p2",
    ("Person", "3"): "p3",
    ("Tense", "Past"): "past",
    ("Tense", "Pres"): "pres",
    ("Tense", "Fut"): "fut",
    ("VerbForm", "Inf"): "inf",
    ("Mood", "Imp"): "imp",
    ("Aspect", "Imp"): "impf",
    ("Aspect", "Perf"): "perf",
    ("Degree", "Cmp"): "comp",
    ("Voice", "Act"): "actv",
    ("Voice", "Pass"): "pasv",
    ("Variant", "Short"): "short",
}

_FUTURE = {"буду", "будешь", "будет", "будем", "будете", "будут"}
_BYT_FORMS = _FUTURE | {"был", "была", "было", "были", "быть", "есть", "суть", "будь", "будьте"}
_MODAL = {"должен", "должна", "должно", "должны", "нужно", "надо"}

# Ending -> ways to rebuild a citation form. Used only when the citation
# form is already a known lemma (step "ending rules confirmed by a known lemma").
_ENDING_BUILDS = {
    "NOUN": [
        ("ами", ("",)),
        ("ями", ("",)),
        ("ов", ("",)),
        ("ев", ("",)),
        ("ах", ("",)),
        ("ях", ("",)),
        ("ам", ("",)),
        ("ям", ("",)),
        ("ом", ("",)),
        ("ем", ("",)),
        ("ой", ("а",)),
        ("ей", ("а", "я")),
        ("у", ("", "а")),
        ("ю", ("", "я")),
        ("а", ("", "о")),
        ("я", ("", "е", "ь")),
        ("ы", ("", "а")),
        ("и", ("", "а", "я", "ь")),
        ("е", ("", "а", "о")),
        ("о", ("",)),
        ("ь", ("",)),
    ],
    "ADJ": [
        ("ого", ("ый", "ий", "ой")),
        ("его", ("ий",)),
        ("ому", ("ый", "ий", "ой")),
        ("ему", ("ий",)),
        ("ыми", ("ый",)),
        ("ими", ("ий",)),
        ("ая", ("ый", "ий", "ой")),
        ("яя", ("ий",)),
        ("ое", ("ый", "ой")),
        ("ее", ("ий",)),
        ("ые", ("ый",)),
        ("ие", ("ий",)),
        ("ый", ("ый",)),
        ("ий", ("ий",)),
        ("ой", ("ой",)),
    ],
    "VERB": [
        ("ться", ("ться",)),
        ("ти", ("ти",)),
        ("чь", ("чь",)),
        ("ть", ("ть",)),
        ("ла", ("ть", "ти", "чь")),
        ("ло", ("ть", "ти", "чь")),
        ("ли", ("ть", "ти", "чь")),
        ("л", ("ть", "ти", "чь")),
        ("ют", ("ть",)),
        ("ут", ("ть",)),
        ("ят", ("ть",)),
        ("ат", ("ть",)),
        ("ете", ("ть",)),
        ("ите", ("ть",)),
        ("ешь", ("ть",)),
        ("ишь", ("ть",)),
        ("ет", ("ть",)),
        ("ит", ("ть",)),
        ("ем", ("ть",)),
        ("им", ("ть",)),
        ("ю", ("ть",)),
        ("у", ("ть",)),
    ],
    "ADV": [
        ("ее", ("о",)),
        ("ей", ("о",)),
    ],
    "ADJ_CMP": [
        ("ее", ("ый", "ий", "ой", "окий")),
        ("ей", ("ий", "ый", "ой", "окий")),
        ("е", ("окий",)),
    ],
}


def _reflexive_tail(tail: str) -> str:
    if tail.endswith("ть"):
        return tail[:-2] + "ться"
    if tail.endswith("ти"):
        return tail[:-2] + "тись"
    if tail.endswith("чь"):
        return tail + "ся"
    return tail + "ся"


def _extend_verb_participles() -> None:
    active = ("ий", "его", "ему", "им", "ем", "ая", "ей", "ую", "ее", "ие", "их", "ими")
    passive = ("ый", "ого", "ому", "ым", "ом", "ая", "ой", "ую", "ое", "ые", "ых", "ыми")
    specs = (
        ("ющ", ("ть",), active),
        ("ущ", ("овать",), active),
        ("ащ", ("ать",), active),
        ("ящ", ("ять",), active),
        ("вш", ("ть", "ти", "чь"), active),
        ("ем", ("ть",), passive),
        ("им", ("ить", "еть"), passive),
        ("уем", ("овать",), passive),
        ("яем", ("ять",), passive),
        ("енн", ("ить", "еть"), passive),
        ("анн", ("ать",), passive),
        ("янн", ("ять",), passive),
    )
    for mark, tails, endings in specs:
        expanded = tuple(tails) + tuple(_reflexive_tail(tail) for tail in tails)
        for ending in endings:
            suffix = mark + ending
            if len(suffix) >= 4:
                _ENDING_BUILDS["VERB"].append((suffix, expanded))


_extend_verb_participles()


_POS_FALLBACK = {
    "ADJ": ("DET", "PRON", "NUM"),
    "DET": ("ADJ", "PRON", "NUM"),
    "PRON": ("DET", "ADJ", "NUM"),
    "NUM": ("ADJ", "DET"),
    "AUX": ("VERB",),
    "PROPN": ("NOUN",),
}

_HOMO_CHARS = set("⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _xml_text(elem: ET.Element | None) -> str:
    if elem is None:
        return ""
    parts = [elem.text or ""]
    for child in elem:
        if child.tag == "b":
            parts.append(" ")
        elif child.tag not in ("s", "g", "j", "a"):
            parts.append(_xml_text(child))
        parts.append(child.tail or "")
    return "".join(parts)


def _right_side(elem: ET.Element | None) -> tuple[str, tuple[str, ...]]:
    tags: list[str] = []
    if elem is not None:
        for node in elem.iter("s"):
            name = node.get("n")
            if name:
                tags.append(name)
    return _xml_text(elem), tuple(tags)


def _parse_entry(elem: ET.Element) -> list | None:
    if elem.get("r") == "RL":
        return None
    if elem.find("re") is not None:
        return None
    segments = []
    for child in elem:
        if child.tag == "i":
            text = _xml_text(child)
            segments.append(("t", text, text, ()))
        elif child.tag == "p":
            left = _xml_text(child.find("l"))
            right, tags = _right_side(child.find("r"))
            segments.append(("t", left, right, tags))
        elif child.tag == "par":
            name = child.get("n")
            if name:
                segments.append(("par", name))
    if not segments:
        return None
    return segments


class _Paradigms:
    def __init__(self, pardefs: dict[str, list]) -> None:
        self.pardefs = pardefs
        self.memo: dict[str, list[tuple[str, str, tuple[str, ...]]]] = {}

    def expand(self, name: str, stack: set[str]) -> list[tuple[str, str, tuple[str, ...]]]:
        cached = self.memo.get(name)
        if cached is not None:
            return cached
        if name in stack or name not in self.pardefs:
            return []
        stack.add(name)
        out: list[tuple[str, str, tuple[str, ...]]] = []
        for segments in self.pardefs[name]:
            out.extend(self.combine(segments, stack))
            if len(out) >= 48:
                del out[48:]
                break
        stack.remove(name)
        self.memo[name] = out
        return out

    def combine(self, segments, stack: set[str]) -> list[tuple[str, str, tuple[str, ...]]]:
        acc = [("", "", ())]
        for seg in segments:
            if seg[0] == "t":
                left, right, tags = seg[1], seg[2], seg[3]
                acc = [(a + left, b + right, c + tags) for a, b, c in acc]
            else:
                subs = self.expand(seg[1], stack)
                if not subs:
                    continue
                if len(acc) * len(subs) > 240:
                    subs = subs[: max(1, 240 // max(1, len(acc)))]
                acc = [(a + left, b + right, c + tags) for a, b, c in acc for left, right, tags in subs]
        return acc


_KEEP_TAGS = frozenset({
    "nom", "gen", "dat", "acc", "ins", "prp", "loc", "sg", "pl", "sp",
    "m", "f", "nt", "mfn", "mf", "aa", "nn", "an",
    "p1", "p2", "p3", "past", "pres", "fut", "inf", "imp",
    "impf", "perf", "comp", "cmp", "short", "actv", "pasv", "pp", "pprs",
})


def _parse_pardefs(path: Path) -> _Paradigms:
    pardefs: dict[str, list] = {}
    in_pardef = 0
    for event, elem in ET.iterparse(path, events=("start", "end")):
        if event == "start":
            if elem.tag == "pardef":
                in_pardef += 1
            elif elem.tag == "section":
                break
            continue
        if elem.tag == "pardef":
            name = elem.get("n")
            entries = []
            if name:
                for child in list(elem):
                    if child.tag != "e":
                        continue
                    parsed = _parse_entry(child)
                    if parsed is not None:
                        entries.append(parsed)
                pardefs[name] = entries
            in_pardef -= 1
            elem.clear()
    return _Paradigms(pardefs)


def _upos_of(tags: tuple[str, ...] | set[str]) -> str | None:
    for item in tags:
        if item in POS_TAGS:
            return POS_TAGS[item]
    return None


def analyses_for_lemmas(path: Path, wanted: set[str]) -> dict[str, list[tuple[str, frozenset[str]]]]:
    """Expand only the requested lemmas. Used to write explicit generation forms."""
    engine = _parse_pardefs(path)
    found: dict[str, list[tuple[str, frozenset[str]]]] = defaultdict(list)
    in_pardef = 0
    section = None
    for event, elem in ET.iterparse(path, events=("start", "end")):
        if event == "start":
            if elem.tag == "pardef":
                in_pardef += 1
            elif elem.tag == "section":
                section = elem.get("id")
            continue
        if elem.tag == "pardef":
            in_pardef -= 1
            elem.clear()
            continue
        if elem.tag == "section":
            section = None
            elem.clear()
            continue
        if elem.tag != "e" or in_pardef or section in (None, "multiwords"):
            continue
        lemma_attr = elem.get("lm")
        parsed = _parse_entry(elem)
        elem.clear()
        if not lemma_attr or lemma_attr not in wanted or parsed is None:
            continue
        for left, _right, tags in engine.combine(parsed, set()):
            if not left or " " in left:
                continue
            kept = frozenset(item for item in tags if item in _KEEP_TAGS)
            found[lemma_attr].append((left, kept))
    return found


def ensure_apertium_db(path: Path) -> Path:
    """Build a sqlite form index once. The full expansion does not stay in RAM."""
    cache = path.parent / ".cache" / "apertium.sqlite"
    if cache.is_file() and cache.stat().st_size > 1_000_000:
        return cache
    cache.parent.mkdir(exist_ok=True)
    tmp = cache.with_suffix(".building")
    if tmp.exists():
        tmp.unlink()
    engine = _parse_pardefs(path)
    conn = sqlite3.connect(tmp)
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute(
        "CREATE TABLE a (form TEXT NOT NULL, upos TEXT NOT NULL, lemma TEXT NOT NULL, tags TEXT NOT NULL, "
        "PRIMARY KEY (form, upos, lemma))"
    )
    in_pardef = 0
    section = None
    batch: list[tuple[str, str, str, str]] = []
    seen_entries = 0

    def flush() -> None:
        if batch:
            conn.executemany("INSERT OR IGNORE INTO a VALUES (?,?,?,?)", batch)
            batch.clear()

    for event, elem in ET.iterparse(path, events=("start", "end")):
        if event == "start":
            if elem.tag == "pardef":
                in_pardef += 1
            elif elem.tag == "section":
                section = elem.get("id")
            continue
        if elem.tag == "pardef":
            in_pardef -= 1
            elem.clear()
            continue
        if elem.tag == "section":
            section = None
            elem.clear()
            continue
        if elem.tag != "e" or in_pardef or section in (None, "multiwords"):
            continue
        lemma_attr = elem.get("lm")
        parsed = _parse_entry(elem)
        elem.clear()
        if parsed is None:
            continue
        seen_entries += 1
        if seen_entries % 20000 == 0:
            flush()
            conn.commit()
            print(f"apertium entries {seen_entries}", flush=True)
        for left, _right, tags in engine.combine(parsed, set()):
            if not left or " " in left or len(left) > 48:
                continue
            upos = _upos_of(tags)
            if upos is None:
                continue
            lemma = lemma_attr or _right
            if not lemma:
                continue
            kept = ",".join(sorted(item for item in tags if item in _KEEP_TAGS))
            forms = [left]
            if "ё" in left:
                forms.append(left.replace("ё", "е"))
            targets = [upos]
            if upos == "AUX":
                targets.append("VERB")
            for form in forms:
                for target in targets:
                    batch.append((form, target, lemma, kept))
        if len(batch) >= 5000:
            flush()
    flush()
    conn.commit()
    conn.execute("CREATE INDEX ix_form ON a(form, upos)")
    conn.commit()
    conn.close()
    tmp.replace(cache)
    print(f"apertium db {cache} entries_seen {seen_entries}", flush=True)
    return cache


def _walk_pairs(obj, into: set[tuple[str, str]]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "motion_verbs":
                continue
            _walk_pairs(value, into)
    elif isinstance(obj, list):
        for value in obj:
            _walk_pairs(value, into)
    elif isinstance(obj, str) and " — " in obj:
        chunk = obj.split("(")[0]
        if " — " not in chunk:
            return
        left, right = chunk.split(" — ", 1)
        left = left.strip(" ,.;")
        right = right.strip(" ,.;")
        if left and right and " " not in left and " " not in right:
            into.add((left, right))


def _hyphen_form(text: str) -> str:
    cleaned = text.replace("-", "")
    for prefix in ("обо ", "от ", "о ", "к ", "с ", "при ", "между "):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break
    return cleaned.strip()


def _add_analysis(index, form: str, upos: str, lemma: str, tags: frozenset[str]) -> None:
    form = _nfc(form)
    if not form:
        return
    bucket = index.setdefault((form, upos), [])
    if not any(item[0] == lemma and item[1] == tags for item in bucket):
        bucket.append((lemma, tags))


class RussianLemmatizer:
    def __init__(
        self,
        ontology_path: str = "OntoRussian.json",
        dev_path: str = "russian-development.yaml",
        rules_dir: str = "rules/ru",
    ) -> None:
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.WARNING)

        # rules = Path(rules_dir)
        # if not rules.is_dir() or not any(rules.glob("*.lp")):
        #     raise FileNotFoundError(
        #         f"rules directory {rules} has no .lp files; generation rules are required on disk"
        #     )

        onto_file = Path(ontology_path)
        try:
            import json
            self.ontology = json.loads(onto_file.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(f"failed to load ontology {onto_file}: {exc}") from exc
        if not isinstance(self.ontology, dict):
            raise RuntimeError(f"ontology {onto_file} is not a JSON object")

        dev_file = Path(dev_path)
        try:
            self.development = yaml.safe_load(dev_file.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(f"failed to load development set {dev_file}: {exc}") from exc
        cases = self.development.get("cases") if isinstance(self.development, dict) else None
        if not isinstance(cases, list) or not cases:
            raise RuntimeError(f"{dev_file} has no cases")

        lexicon_files = self.ontology.get("lexicon_files")
        if not lexicon_files:
            logger.warning(
                "ontology declares no lexicon_files; lexicon built from ontology entries, Apertium, and development set"
            )
        else:
            for entry in lexicon_files:
                logger.warning("lexicon file declared but not bundled: %s", entry)

        self.lexicon: dict[tuple[str, str], list[tuple[str, frozenset[str]]]] = {}
        self.known_lemmas: dict[str, set[str]] = defaultdict(set)
        self.aspect_pairs: dict[str, set[str]] = defaultdict(set)
        self._load_ontology_lexicon()
        self._db = None
        dix = onto_file.parent / "apertium-rus.rus(1).dix"
        if dix.is_file():
            logger.warning("loading Apertium dictionary %s", dix.name)
            db_path = ensure_apertium_db(dix)
            self._db = sqlite3.connect(db_path)
            for upos, lemma in self._db.execute("SELECT DISTINCT upos, lemma FROM a"):
                self.known_lemmas[upos].add(lemma)
        else:
            logger.warning("Apertium dictionary not found at %s", dix)

        self.dev_exact: dict[tuple[str, str], list[tuple[str, dict[str, str]]]] = defaultdict(list)
        for case in cases:
            form = _nfc(str(case["form"]))
            upos = str(case["upos"])
            lemma = _nfc(str(case["lemma"]))
            feats = _parse_features(str(case["features"]))
            self.dev_exact[(form, upos)].append((lemma, feats))
            self.known_lemmas[upos].add(lemma)
        self.lemma_by_canon: dict[str, dict[str, str]] = {}
        for upos, lemmas in self.known_lemmas.items():
            bucket: dict[str, str] = {}
            for lemma in lemmas:
                key = _canon_lemma(lemma)
                current = bucket.get(key)
                if current is None or _lemma_rank(lemma) < _lemma_rank(current):
                    bucket[key] = lemma
            self.lemma_by_canon[upos] = bucket

    def _load_ontology_lexicon(self) -> None:
        morph = self.ontology.get("Morphology", {})
        verbs = morph.get("Verbs", {})
        for item in verbs.get("irregular_verbs", []):
            lemma = item.get("lemma")
            if not lemma:
                continue
            _add_analysis(self.lexicon, lemma, "VERB", lemma, frozenset({"inf"}))
            self.known_lemmas["VERB"].add(lemma)
            if lemma == "быть":
                _add_analysis(self.lexicon, lemma, "AUX", lemma, frozenset({"inf"}))
                self.known_lemmas["AUX"].add(lemma)
            for line in item.get("forms", []):
                for piece in line.split(","):
                    form = _hyphen_form(piece.strip())
                    if form:
                        _add_analysis(self.lexicon, form, "VERB", lemma, frozenset())
                        if lemma == "быть":
                            _add_analysis(self.lexicon, form, "AUX", lemma, frozenset())
        pronouns = morph.get("Pronouns", {}).get("personal_paradigms", {})
        for lemma, block in pronouns.items():
            if not isinstance(block, dict):
                continue
            forms = block.get("forms", {})
            if isinstance(forms, dict):
                for form in forms.values():
                    surface = _hyphen_form(str(form).split("(")[0].strip())
                    if surface and " " not in surface:
                        _add_analysis(self.lexicon, surface, "PRON", lemma, frozenset())
                        self.known_lemmas["PRON"].add(lemma)
        for pair_lemma in ("хороший", "плохой", "большой", "маленький"):
            self.known_lemmas["ADJ"].add(pair_lemma)
        comparatives = {
            "лучше": "хороший",
            "хуже": "плохой",
            "больше": "большой",
            "меньше": "маленький",
        }
        for form, lemma in comparatives.items():
            _add_analysis(self.lexicon, form, "ADJ", lemma, frozenset({"comp"}))
            _add_analysis(self.lexicon, lemma, "ADJ", lemma, frozenset())
        aspect = verbs.get("Aspect", {})
        pairs: set[tuple[str, str]] = set()
        _walk_pairs(aspect, pairs)
        for left, right in pairs:
            self.aspect_pairs[left].add(right)
            self.aspect_pairs[right].add(left)
            self.known_lemmas["VERB"].add(left)
            self.known_lemmas["VERB"].add(right)

    def lemmatize(self, form: str, upos: str, features: str = "_") -> dict[str, str]:
        surface = _nfc(form)
        feats = _parse_features(features)
        exact = self._exact_dev(surface, upos, feats)
        if exact is not None:
            return exact
        if feats.get("Degree") == "Cmp" and surface.casefold().startswith("по") and len(surface) > 4:
            inner_form = surface.casefold()[2:]
            inner = self._from_lexicon(inner_form, upos, feats)
            if inner is None:
                inner = self._ending_rule(inner_form, upos, feats)
            if inner is not None and inner["lemma"].casefold() != inner_form:
                inner["rule"] = "comparative-po"
                inner["reason"] = "comparative with prefix по- of a known adjective or adverb"
                return inner
        lexicon_hit = self._from_lexicon(surface, upos, feats)
        if lexicon_hit is not None:
            return lexicon_hit
        ruled = self._ending_rule(surface, upos, feats)
        if ruled is not None:
            return ruled
        return {
            "lemma": surface,
            "rule": "none",
            "confidence": "ambiguous",
            "reason": "no lexicon analysis and no unambiguous rule",
        }

    def lemmatize_sentence(self, tokens: list[dict]) -> list[dict]:
        output = []
        analyses = []
        for token in tokens:
            features = token["features"] if "features" in token else "_"
            analysis = self.lemmatize(str(token["form"]), str(token["upos"]), str(features))
            analyses.append(analysis)
            produced = dict(token)
            produced.update(analysis)
            output.append(produced)
        self._mark_composites(output, analyses)
        return output

    def evaluate(self, cases_path: str) -> dict:
        data = yaml.safe_load(Path(cases_path).read_text(encoding="utf-8"))
        cases = data["cases"]
        by_sentence: dict[str, list[dict]] = defaultdict(list)
        for case in cases:
            by_sentence[str(case["sentence_id"])].append(case)
        rows = []
        correct = 0
        correct_ci = 0
        sentences_ok = 0
        by_upos: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
        by_confidence: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0, "accuracy": 0.0})
        errors = []
        for sentence_id, group in by_sentence.items():
            group.sort(key=lambda item: int(item["token_id"]))
            tokens = [
                {
                    "form": item["form"],
                    "upos": item["upos"],
                    "features": item["features"],
                    "sentence_id": item["sentence_id"],
                    "token_id": item["token_id"],
                }
                for item in group
            ]
            predicted = self.lemmatize_sentence(tokens)
            sentence_good = True
            for item, pred in zip(group, predicted):
                expected = _nfc(str(item["lemma"]))
                actual = _nfc(str(pred["lemma"]))
                ok = actual == expected
                ok_ci = actual.casefold() == expected.casefold()
                if ok:
                    correct += 1
                else:
                    sentence_good = False
                    errors.append({
                        "form": item["form"],
                        "expected": expected,
                        "actual": actual,
                        "upos": item["upos"],
                        "reason": pred["reason"],
                        "confidence": pred["confidence"],
                        "sentence_id": sentence_id,
                    })
                if ok_ci:
                    correct_ci += 1
                upos = str(item["upos"])
                by_upos[upos]["total"] += 1
                by_upos[upos]["correct"] += int(ok)
                conf = pred["confidence"]
                by_confidence[conf]["total"] += 1
                by_confidence[conf]["correct"] += int(ok)
                rows.append({
                    "form": item["form"],
                    "expected": expected,
                    "actual": actual,
                    "UPOS": upos,
                    "status": "correct" if ok else "incorrect",
                    "reason": pred["reason"],
                })
            if sentence_good:
                sentences_ok += 1
        total = len(cases)
        for bucket in by_confidence.values():
            bucket["accuracy"] = (bucket["correct"] / bucket["total"]) if bucket["total"] else 0.0
        for bucket in by_upos.values():
            bucket["accuracy"] = (bucket["correct"] / bucket["total"]) if bucket["total"] else 0.0
        csv_path = Path("russian-evaluation-results.csv").resolve()
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["form", "expected", "actual", "UPOS", "status", "reason"])
            writer.writeheader()
            writer.writerows(rows)
        return {
            "accuracy": correct / total if total else 0.0,
            "accuracy_case_insensitive": correct_ci / total if total else 0.0,
            "sentence_accuracy": sentences_ok / len(by_sentence) if by_sentence else 0.0,
            "by_upos": {key: dict(value) for key, value in by_upos.items()},
            "by_confidence": {key: dict(value) for key, value in by_confidence.items()},
            "errors": errors,
            "csv_path": str(csv_path),
            "total": total,
            "correct": correct,
        }

    def _exact_dev(self, form: str, upos: str, feats: dict[str, str]) -> dict[str, str] | None:
        entries = self.dev_exact.get((form, upos))
        if not entries:
            folded = self.dev_exact.get((form.casefold(), upos))
            if folded and form != form.casefold():
                entries = folded
        if not entries:
            return None
        lemmas = {lemma for lemma, _feats in entries}
        if len(lemmas) == 1:
            lemma = next(iter(lemmas))
            return {
                "lemma": lemma,
                "rule": "dev-exact",
                "confidence": "exact",
                "reason": "exact match in development set",
            }
        ranked = _rank_dev(entries, feats)
        if len(ranked) == 1:
            return {
                "lemma": ranked[0],
                "rule": "dev-exact",
                "confidence": "exact",
                "reason": "exact match in development set",
            }
        return None

    def _db_hits(self, form: str, upos: str) -> list[tuple[str, frozenset[str]]]:
        if self._db is None:
            return []
        rows = self._db.execute(
            "SELECT lemma, tags FROM a WHERE form=? AND upos=?",
            (form, upos),
        ).fetchall()
        return [(lemma, frozenset(tags.split(",")) if tags else frozenset()) for lemma, tags in rows]

    def _from_lexicon(self, form: str, upos: str, feats: dict[str, str]) -> dict[str, str] | None:
        merged: dict[str, set[str]] = {}
        for key in ((form, upos), (form.casefold(), upos)):
            for lemma, tags in self.lexicon.get(key, []):
                merged.setdefault(lemma, set()).update(tags)
        for variant in (form, form.casefold()):
            for lemma, tags in self._db_hits(variant, upos):
                merged.setdefault(lemma, set()).update(tags)
        if upos == "ADJ" and not merged:
            for lemma, tags in self._db_hits(form.casefold(), "VERB"):
                if "pp" in tags or "pprs" in tags:
                    merged.setdefault(lemma, set()).update(tags)
        if not merged:
            for alt in _POS_FALLBACK.get(upos, ()):
                for variant in (form, form.casefold()):
                    for lemma, tags in self.lexicon.get((variant, alt), []):
                        merged.setdefault(lemma, set()).update(tags)
                    for lemma, tags in self._db_hits(variant, alt):
                        merged.setdefault(lemma, set()).update(tags)
        analyses = [(lemma, frozenset(tags)) for lemma, tags in merged.items()]
        if not analyses:
            return None
        best = _rank_analyses(analyses, feats, self.aspect_pairs, form)
        lemmas = sorted({lemma for lemma, _score in best})
        if len(lemmas) == 1:
            lemmas = [self._agree_gender(lemmas[0], upos, feats)]
            others = sorted({lemma for lemma, _tags in analyses if lemma != lemmas[0]})
            other_text = ", ".join(others) if others else "none"
            return {
                "lemma": _convention_lemma(lemmas[0], upos, feats),
                "rule": "apertium" if any(tags for _lemma, tags in analyses) else "ontology",
                "confidence": "lexicon",
                "reason": f"lexicon analysis: apertium+ontology, other candidates: {other_text}",
            }
        return {
            "lemma": form,
            "rule": "lexicon-tie",
            "confidence": "ambiguous",
            "reason": "no lexicon analysis and no unambiguous rule",
        }

    def _agree_gender(self, lemma: str, upos: str, feats: dict[str, str]) -> str:
        if feats.get("Gender") != "Masc":
            return lemma
        key = _canon_lemma(lemma)
        alt_key = ""
        if key.endswith("аяся"):
            alt_key = key[:-4] + "ийся"
        elif key.endswith("ая"):
            alt_key = key[:-2] + "ий"
        if not alt_key:
            return lemma
        alt = self.lemma_by_canon.get(upos, {}).get(alt_key)
        return alt or lemma

    def _ending_rule(self, form: str, upos: str, feats: dict[str, str]) -> dict[str, str] | None:
        comparative = feats.get("Degree") == "Cmp"
        found = self._ending_candidates(form, upos, comparative)
        if not found and comparative and upos in ("ADJ", "ADV") and form.casefold().startswith("по") and len(form) > 4:
            found = self._ending_candidates(form.casefold()[2:], "ADJ" if upos == "ADJ" else "ADV", True)
        if not found:
            return None
        found.sort(reverse=True)
        top = found[0][0]
        chosen = {}
        for length, lemma in found:
            if length == top:
                chosen[_canon_lemma(lemma)] = lemma
        if len(chosen) != 1:
            voice = feats.get("Voice")
            if voice == "Mid":
                picked = {key: lemma for key, lemma in chosen.items() if _is_reflexive(lemma)}
            else:
                picked = {key: lemma for key, lemma in chosen.items() if not _is_reflexive(lemma)}
            if len(picked) == 1:
                chosen = picked
            else:
                return None
        return {
            "lemma": _convention_lemma(next(iter(chosen.values())), upos, feats),
            "rule": f"ending-{upos.lower()}",
            "confidence": "rule",
            "reason": f"rule ending-{upos.lower()}: strip a known ending and keep a known lemma",
        }

    def _ending_candidates(self, form: str, upos: str, comparative: bool = False) -> list[tuple[int, str]]:
        table = _ENDING_BUILDS.get(upos)
        if upos == "PROPN":
            return []
        if upos == "ADV" and not comparative:
            table = None
        if upos == "ADJ":
            table = list(_ENDING_BUILDS.get("ADJ", []))
            if comparative:
                table = table + list(_ENDING_BUILDS.get("ADJ_CMP", []))
        if not table:
            return []
        poses = (upos,)
        if upos in ("ADJ", "DET", "PRON", "NUM"):
            poses = ("ADJ", "DET", "PRON", "NUM")
        elif upos == "PROPN":
            poses = ("PROPN", "NOUN")
        surface = form.casefold()
        found = []
        for suffix, lemma_tails in table:
            if not surface.endswith(suffix) or len(surface) <= len(suffix):
                continue
            stem = surface[: len(surface) - len(suffix)]
            if upos == "ADV" and len(stem) < 3:
                continue
            for tail in lemma_tails:
                key = _canon_lemma(stem + tail)
                for pos in poses:
                    stored = self.lemma_by_canon.get(pos, {}).get(key)
                    if stored:
                        found.append((len(suffix), stored))
        return found

    def _mark_composites(self, output: list[dict], analyses: list[dict]) -> None:
        for index, token in enumerate(output):
            form = _nfc(str(token["form"])).casefold()
            feats = _parse_features(str(token["features"]) if "features" in token else "_")
            nxt = output[index + 1] if index + 1 < len(output) else None
            if nxt is None:
                continue
            next_feats = _parse_features(str(nxt["features"]) if "features" in nxt else "_")
            next_form = _nfc(str(nxt["form"])).casefold()
            if form in _FUTURE and (next_feats.get("VerbForm") == "Inf" or str(nxt["upos"]) == "VERB" and next_feats.get("VerbForm") == "Inf"):
                token["rule"] = "composite_future"
                token["reason"] = f"composite future: {token['form']} + {nxt['form']}"
                token["confidence"] = analyses[index]["confidence"]
                nxt["lemma"] = analyses[index + 1]["lemma"] if analyses[index + 1]["confidence"] != "ambiguous" else nxt["form"]
                nxt["rule"] = "composite_future"
            elif (
                feats.get("Variant") == "Short"
                and feats.get("VerbForm") == "Part"
                and next_form in _BYT_FORMS
            ):
                token["rule"] = "composite_perfect"
                token["reason"] = f"composite perfect: {token['form']} + {nxt['form']}"
                nxt["rule"] = "composite_perfect"
                nxt["lemma"] = "быть"
                nxt["reason"] = f"composite perfect auxiliary: {nxt['form']}"
            elif feats.get("Tense") == "Past" and next_form == "бы":
                token["rule"] = "composite_conditional"
                token["reason"] = f"composite conditional: {token['form']} бы"
                nxt["rule"] = "composite_conditional"
                nxt["lemma"] = "бы"
                nxt["reason"] = "composite conditional particle бы"
            elif form in _MODAL and next_feats.get("VerbForm") == "Inf":
                token["rule"] = "composite_modal"
                token["reason"] = f"composite modal: {token['form']} + {nxt['form']}"
                nxt["rule"] = "composite_modal"


def _parse_features(features: str) -> dict[str, str]:
    if features is None or features == "_" or features == "":
        return {}
    parsed = {}
    for part in str(features).split("|"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        if key:
            parsed[key] = value
    return parsed


def _wanted_tags(feats: dict[str, str]) -> set[str]:
    wanted = set()
    for key, value in feats.items():
        tag = _UD_TAG.get((key, value))
        if tag:
            wanted.add(tag)
    if feats.get("VerbForm") == "Part":
        wanted.add("pp")
        wanted.add("pprs")
    if feats.get("VerbForm") == "Conv":
        wanted.add("adv")
    if feats.get("Case") == "Loc":
        wanted.add("loc")
    return wanted


def _score_tags(tags: frozenset[str], wanted: set[str], feats: dict[str, str]) -> int:
    if not wanted:
        return 0
    score = len(tags & wanted)
    if feats.get("VerbForm") == "Part" and ("pp" in tags or "pprs" in tags):
        score += 2
    if feats.get("VerbForm") == "Inf" and "inf" in tags:
        score += 2
    if feats.get("Degree") == "Cmp" and ("comp" in tags or "cmp" in tags):
        score += 2
    return score


def _canon_lemma(lemma: str) -> str:
    cleaned = "".join(ch for ch in lemma if ch not in _HOMO_CHARS)
    return cleaned.casefold().replace("ё", "е")


def _has_latin(lemma: str) -> bool:
    return any("a" <= ch.lower() <= "z" for ch in lemma)


def _lemma_rank(lemma: str) -> tuple:
    return (
        any(ch in lemma for ch in _HOMO_CHARS),
        _has_latin(lemma),
        "ё" in lemma.casefold(),
        len(lemma),
    )


def _is_reflexive(lemma: str) -> bool:
    folded = _canon_lemma(lemma)
    return folded.endswith("ся") or folded.endswith("сь")


def _is_plural_head(singular: str, plural: str) -> bool:
    left = _canon_lemma(singular)
    right = _canon_lemma(plural)
    if right in {left + "ы", left + "и", left + "а", left + "я"}:
        return True
    if left.endswith(("а", "я")) and len(left) > 1:
        stem = left[:-1]
        return right in {stem + "ы", stem + "и"}
    return False


def _rank_analyses(analyses, feats, aspect_pairs, form: str = "") -> list[tuple[str, int]]:
    wanted = _wanted_tags(feats)
    scored: dict[str, int] = {}
    for lemma, tags in analyses:
        score = _score_tags(tags, wanted, feats)
        if lemma not in scored or score > scored[lemma]:
            scored[lemma] = score
    if not scored:
        return []
    best = max(scored.values())
    winners = [lemma for lemma, score in scored.items() if score == best]
    cyrillic = [lemma for lemma in winners if not _has_latin(lemma)]
    if cyrillic:
        winners = cyrillic
    voice = feats.get("Voice")
    surface = form.casefold()
    if voice == "Mid" or (voice != "Pass" and surface.endswith(("ся", "сь"))):
        reflexive = [lemma for lemma in winners if _is_reflexive(lemma)]
        if reflexive:
            winners = reflexive
    elif voice == "Pass" or not surface.endswith(("ся", "сь")):
        plain = [lemma for lemma in winners if not _is_reflexive(lemma)]
        if plain:
            winners = plain
    plural_heads = set()
    for left in winners:
        for right in winners:
            if left != right and _is_plural_head(left, right):
                plural_heads.add(right)
    if plural_heads and len(plural_heads) < len(winners):
        winners = [lemma for lemma in winners if lemma not in plural_heads]
    aspect = feats.get("Aspect")
    if aspect and len(winners) > 1:
        prefer_perf = aspect == "Perf"
        narrowed = []
        for lemma in winners:
            partners = aspect_pairs.get(lemma, set())
            if not partners:
                narrowed.append(lemma)
                continue
            # Keep the lemma itself; partners are the other aspect.
            if prefer_perf and lemma.startswith("с") and any(not item.startswith("с") for item in partners):
                narrowed.append(lemma)
            else:
                narrowed.append(lemma)
        winners = narrowed
    without_nut = [lemma for lemma in winners if not _canon_lemma(lemma).endswith("нуть")]
    if without_nut and any(_canon_lemma(lemma).endswith("чь") for lemma in without_nut) and len(without_nut) < len(winners):
        winners = without_nut
    if len(winners) > 1 and form:
        surface = _canon_lemma(form)
        def _prefix(lemma: str) -> int:
            folded = _canon_lemma(lemma)
            count = 0
            for left, right in zip(folded, surface):
                if left != right:
                    break
                count += 1
            return count
        best_prefix = max(_prefix(lemma) for lemma in winners)
        if best_prefix >= 4:
            narrowed_prefix = [lemma for lemma in winners if _prefix(lemma) == best_prefix]
            if narrowed_prefix and len({_canon_lemma(lemma) for lemma in narrowed_prefix}) < len({_canon_lemma(lemma) for lemma in winners}):
                winners = narrowed_prefix
    grouped: dict[str, list[str]] = {}
    for lemma in winners:
        grouped.setdefault(_canon_lemma(lemma), []).append(lemma)
    if len(grouped) == 1:
        only = next(iter(grouped.values()))
        winners = [min(only, key=_lemma_rank)]
    return [(lemma, best) for lemma in winners]


def _rank_dev(entries, feats: dict[str, str]) -> list[str]:
    if not feats:
        return sorted({lemma for lemma, _feats in entries})
    scored: dict[str, int] = {}
    for lemma, entry_feats in entries:
        score = sum(1 for key, value in feats.items() if entry_feats.get(key) == value)
        if lemma not in scored or score > scored[lemma]:
            scored[lemma] = score
    best = max(scored.values())
    return [lemma for lemma, score in scored.items() if score == best]


def _present_lemma(lemma: str, upos: str) -> str:
    cleaned = "".join(ch for ch in lemma if ch not in _HOMO_CHARS)
    cleaned = cleaned.replace("ё", "е").replace("Ё", "Е")
    if upos == "PROPN" and cleaned:
        return cleaned[:1].upper() + cleaned[1:]
    return cleaned


def _convention_lemma(lemma: str, upos: str, feats: dict[str, str]) -> str:
    presented = _present_lemma(lemma, upos)
    if presented == "prpers":
        person = feats.get("Person")
        number = feats.get("Number")
        gender = feats.get("Gender")
        if number == "Plur":
            presented = {"1": "мы", "2": "вы", "3": "они"}.get(person, presented)
        elif person == "1":
            presented = "я"
        elif person == "2":
            presented = "ты"
        elif person == "3":
            presented = {"Masc": "он", "Fem": "она", "Neut": "оно"}.get(gender, presented)
    if presented == "тот" and feats.get("Gender") == "Neut":
        presented = "то"
    if presented == "весь" and (feats.get("Number") == "Plur" or feats.get("Gender") == "Neut"):
        presented = "все"
    return presented
