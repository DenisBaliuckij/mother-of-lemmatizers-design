# Language recognition

Recognition answers two questions for every segment: which known language is it, and is it perhaps none of them. The second question matters most here, because a closed-set classifier always returns some label, even for a language it has never seen.

## Algorithm

1.  **Script first.** The dominant Unicode script restricts the candidate set (a Cyrillic text cannot be Hindi). Script is part of the label, as in GlotLID (`kaz_Cyrl` vs `kaz_Latn`).
2.  **Closed-set classification.** GlotLID v3 (fastText, 2,102 language–script labels, trained on 1,832 languages) returns the top-k labels with probabilities. OpenLID-v3 is added as a second vote because it was tuned for precision among closely related languages. Probabilities are calibrated per label (temperature scaling on held-out data) so that thresholds mean the same thing for every language.
3.  **Mixed-language text.** Segments are scored in sliding windows. MaskLID removes the features of the dominant language and re-classifies the remainder, which reveals an embedded second language without any extra training.
4.  **Open-set rejection.** A segment is marked *unknown* when any of these holds: the calibrated top probability is below τ<sub>p</sub>; the entropy of the top-k distribution is above τ<sub>H</sub>; or the text is an outlier for the winning label, i.e. its character n-gram perplexity under that language's model is far above the perplexity of that language's own validation texts (z-score above τ<sub>z</sub>). The third test catches the dangerous case: a confident but wrong label for a relative of the true language.
5.  **Document-level smoothing.** Neighbouring segments rarely switch language, so labels are smoothed with a simple HMM over segments (switch penalty); isolated low-confidence flips are overruled.

```mermaid
flowchart LR
  S["Segment"] --> SC["Script detection"]
  SC --> G["GlotLID top-k<br/>calibrated"]
  SC --> O["OpenLID vote"]
  G --> E{"Ensemble<br/>p, entropy"}
  O --> E
  E --> M["MaskLID pass<br/>second language?"]
  M --> Z{"Outlier test<br/>n-gram perplexity z-score"}
  Z -->|"in-distribution"| K["Known language label"]
  Z -->|"reject"| U["Unknown<br/>+ LID posterior kept as similarity signal"]
  K --> H["HMM smoothing across segments"]
  U --> H
  classDef inferred fill:#f5ebd8,stroke:#a9741c,stroke-width:2px,stroke-dasharray:5 3,color:#1f2421
  class U inferred
```

*Figure 2. Recognition pipeline per segment. A rejected segment keeps its full probability distribution: it becomes the first similarity signal for finding relatives.*

    # language recognition for one document
    def recognise(doc):
        segments = segment(normalise(doc))
        labels = []
        for seg in segments:
            script = dominant_script(seg)
            dist = ensemble(glotlid.topk(seg, 20), openlid.topk(seg, 20), allowed_script=script)
            dist = calibrate(dist)                                   # per-label temperature
            top, p = dist.best()
            z = perplexity_zscore(seg, ngram_model[top])            # outlier for the winning label?
            if p < TAU_P or entropy(dist) > TAU_H or z > TAU_Z:
                labels.append(Unknown(posterior=dist, script=script))
            else:
                second = masklid(seg, dominant=top)                  # code-switching
                labels.append(Known(top, p, embedded=second))
        return hmm_smooth(labels, switch_penalty=SWITCH)
