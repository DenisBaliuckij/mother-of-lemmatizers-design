# Input and output

The same JSON contract serves every tier, so callers never need to know how a lemma was produced:

    POST /lemmatize
    { "text": "Kharia text or anything else…", "hint_language": null }

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

For an unknown language, `language.status` is `"unknown"` and the block adds `donors` (ranked relatives with scores) and `tree_position` (the estimated Glottolog node).
