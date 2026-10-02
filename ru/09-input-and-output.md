# Вход и выход

Один и тот же JSON-контракт обслуживает все уровни, поэтому вызывающей стороне не нужно знать, как получена лемма:

    POST /lemmatize
    { "text": "Текст на языке кхариа или любом другом…", "hint_language": null }

    200 OK
    {
      "segments": [
        { "span": [0, 118],
          "language": { "glottocode": "khar1287", "iso639_3": "khr", "status": "known",
                        "confidence": 0.93, "embedded": null },
          "tier": "B",
          "grammar": { "id": "khar1287@2026-09-27", "status": "provisional",
                       "sources": ["catalog:2932", "induced"] },
          "tokens": [
            { "form": "…", "lemma": "…", "pos": "NOUN", "features": "Case=Obl|Number=Sing",
              "confidence": 0.81, "rule": "noun_obl_sg", "origin": "extracted" }
          ] }
      ]
    }

Для неизвестного языка `language.status` равен `"unknown"`, а блок дополняется полями `donors` (ранжированные родственники с оценками) и `tree_position` (оценённый узел Glottolog).
