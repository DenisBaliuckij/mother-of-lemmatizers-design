# -*- coding: utf-8 -*-
"""5-fold sentence split of the lemmatizer. The scored fold is not in the lexicon."""

import json
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from russian_lemmatizer import RussianLemmatizer

ROOT = Path(__file__).resolve().parent


def classify(expected: str, actual: str, pred: dict) -> str:
    if expected.casefold() == actual.casefold() and expected != actual:
        return "lemma-convention"
    if expected.replace("ё", "е").replace("Ё", "Е") == actual.replace("ё", "е").replace("Ё", "Е") and expected != actual:
        return "yo-bridge"
    rule = pred["rule"]
    if rule.startswith("composite"):
        return "composite"
    if rule == "lexicon-tie":
        return "homograph"
    if pred["confidence"] == "ambiguous":
        return "missing-lexicon"
    if rule.startswith("ending"):
        return "rule-mismatch"
    if pred["confidence"] == "lexicon":
        return "ranking"
    return "other"


def main() -> None:
    data = yaml.safe_load((ROOT / "russian-development.yaml").read_text(encoding="utf-8"))
    cases = data["cases"]
    by_sentence = defaultdict(list)
    for case in cases:
        by_sentence[str(case["sentence_id"])].append(case)
    sentence_ids = sorted(by_sentence)
    folds = {sentence_id: index % 5 for index, sentence_id in enumerate(sentence_ids)}
    per_fold = []
    all_errors = []
    totals = Counter()
    for fold in range(5):
        train = []
        test_ids = []
        for sentence_id, group in by_sentence.items():
            if folds[sentence_id] == fold:
                test_ids.append(sentence_id)
            else:
                train.extend(group)
        train_path = ROOT / f".cache/cv-train-{fold}.yaml"
        train_path.parent.mkdir(exist_ok=True)
        train_path.write_text(
            yaml.safe_dump({"cases": train}, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        lemmatizer = RussianLemmatizer(
            str(ROOT / "OntoRussian.json"),
            str(train_path),
            # str(ROOT / "rules" / "ru"), #ru-lemmatizer
        )
        correct = 0
        total = 0
        sentences_ok = 0
        by_upos = defaultdict(lambda: {"correct": 0, "total": 0})
        by_conf = defaultdict(lambda: {"correct": 0, "total": 0})
        categories = Counter()
        for sentence_id in test_ids:
            group = sorted(by_sentence[sentence_id], key=lambda item: int(item["token_id"]))
            tokens = [
                {"form": item["form"], "upos": item["upos"], "features": item["features"]}
                for item in group
            ]
            predicted = lemmatizer.lemmatize_sentence(tokens)
            sentence_good = True
            for item, pred in zip(group, predicted):
                expected = str(item["lemma"])
                actual = str(pred["lemma"])
                ok = actual == expected
                total += 1
                correct += int(ok)
                upos = str(item["upos"])
                by_upos[upos]["total"] += 1
                by_upos[upos]["correct"] += int(ok)
                by_conf[pred["confidence"]]["total"] += 1
                by_conf[pred["confidence"]]["correct"] += int(ok)
                totals[pred["confidence"]] += 1
                if not ok:
                    sentence_good = False
                    kind = classify(expected, actual, pred)
                    categories[kind] += 1
                    if len(all_errors) < 80 or categories[kind] <= 8:
                        all_errors.append({
                            "fold": fold,
                            "form": item["form"],
                            "expected": expected,
                            "actual": actual,
                            "upos": upos,
                            "features": item["features"],
                            "rule": pred["rule"],
                            "confidence": pred["confidence"],
                            "reason": pred["reason"],
                            "category": kind,
                        })
            if sentence_good:
                sentences_ok += 1
        per_fold.append({
            "fold": fold,
            "sentences": len(test_ids),
            "sentences_ok": sentences_ok,
            "sentence_accuracy": sentences_ok / len(test_ids) if test_ids else 0.0,
            "tokens": total,
            "correct": correct,
            "accuracy": correct / total if total else 0.0,
            "by_upos": {key: dict(value) for key, value in by_upos.items()},
            "by_confidence": {key: dict(value) for key, value in by_conf.items()},
            "categories": dict(categories),
        })
        print(
            f"fold {fold} {correct}/{total} {correct / total if total else 0:.4f} "
            f"sent {sentences_ok}/{len(test_ids)} {dict(categories)}",
            flush=True,
        )
    token_total = sum(item["tokens"] for item in per_fold)
    token_correct = sum(item["correct"] for item in per_fold)
    sentence_total = sum(item["sentences"] for item in per_fold)
    sentence_correct = sum(item["sentences_ok"] for item in per_fold)
    report = {
        "mean_accuracy": token_correct / token_total if token_total else 0.0,
        "sentence_accuracy": sentence_correct / sentence_total if sentence_total else 0.0,
        "correct": token_correct,
        "total": token_total,
        "folds": per_fold,
        "errors": all_errors,
    }
    out = ROOT / "cv-iteration-3.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"mean {token_correct}/{token_total} {report['mean_accuracy']:.4f} "
        f"sentences {sentence_correct}/{sentence_total} {report['sentence_accuracy']:.4f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
