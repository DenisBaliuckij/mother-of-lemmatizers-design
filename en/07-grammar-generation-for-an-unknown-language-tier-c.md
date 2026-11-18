# Grammar generation for an unknown language (Tier C)

This is where the system uses the laws of language change. The working assumption is the comparative method's: related languages descend from a common ancestor, and the differences between them are largely *regular*. If the regular correspondences between the unknown language and its relatives can be learned, the relatives' morphology can be mapped onto the unknown language and then tested against its text. The mechanism is *relative transfer*: ranked donor grammars supply the prior, the correspondences adapt them, and the target text decides what survives.

```mermaid
flowchart TD
  D["Donor grammars<br/>paradigms · affixes · alternations"] --> T2
  U["Unknown-language text"] --> T1
  T1["1 · Align frequent words with donor lexicons<br/>SCA alignment"] --> T2["2 · Learn sound correspondences<br/>LexStat scoring · EM over alignments"]
  T2 --> T3["3 · Transfer affixes<br/>map donor affixes through correspondences"]
  U --> T4["4 · Unsupervised induction<br/>Morfessor segmentation · paradigm clustering"]
  T3 --> T5{"5 · Fit and reconcile<br/>prior from donors × likelihood from text"}
  T4 --> T5
  P["Typological priors<br/>Grambank imputation along the tree<br/>implicational universals"] --> T5
  T5 --> T6["6 · Assemble provisional grammar<br/>citation-form convention · rule templates"]
  T6 --> T7{"7 · Validate<br/>coverage · description length · stability"}
  T7 -->|"improve"| T2
  T7 -->|"accept"| G[("Grammar store<br/>provisional")]
  classDef inferred fill:#f5ebd8,stroke:#a9741c,stroke-width:2px,stroke-dasharray:5 3,color:#1f2421
  classDef known fill:#e4e8f4,stroke:#2e3f7a,stroke-width:2px,color:#1f2421
  class D known
  class T3,T5,T6,G inferred
```

*Figure 4. The grammar generation loop. Steps 2 to 7 repeat until the grammar's coverage and stability stop improving.*

## 0 · Donor selection and weighting

The donors are the ranked relatives returned by section 4, not all of the family. Each candidate carries two distances: a **genealogical** distance read from the Glottolog tree [14] (branch length, or tree-edit distance, to the target's estimated node) and a **typological** distance, the cosine between the target's inferred feature vector and the candidate's Grambank/WALS/URIEL+ vector [13]. The two are combined into a transfer weight, so a close cousin whose structure matches contributes more of its paradigms than a distant or typologically divergent relative. These weights follow the donor through the loop: they scale a donor's vote when correspondences are estimated jointly (step 2) and when transferred affixes are reconciled with the evidence (step 5). When section 4 finds no donor above the cognacy threshold, the donor set is empty and the loop runs on unsupervised induction and typological priors alone.

## 1 · Lexical alignment

The 2,000 most frequent word types of the unknown text are aligned with the lexicons of the donors using sound-class alignment (SCA) [5], which compares words by classes of similar sounds rather than exact letters. Where the orthography is not phonemic, a grapheme-to-phoneme step (Epitran-style) converts both sides to IPA first. Only pairs above a similarity threshold enter the next step.

## 2 · Sound correspondences

From the aligned pairs the system learns a correspondence table: which sound of the donor appears as which sound in the unknown language, in which context (e.g. donor p → target f at the start of a word; donor k → tʃ before front vowels). The LexStat principle [5] is applied: a correspondence counts only if it recurs across many word pairs far more often than in randomly shuffled pairings, which filters out chance lookalikes and most loanwords. Estimation is an EM loop: correspondences re-score the alignments, better alignments refine the correspondences. Where several donors exist, the correspondence patterns across all of them are inferred jointly [5], which is more robust than pairwise tables; probabilistic models of sound change [6] and neural reflex prediction [7] are the same idea pushed further, and supply a fallback estimate when the aligned data are sparse. Each correspondence keeps its support count and its score over the shuffled baseline, which later become the confidence of every affix transferred through it.

## 3 · Affix transfer

Each affix of each donor paradigm is passed through the correspondence table, producing predicted target affixes with probabilities; the prediction's probability is the product of the correspondence scores it used, scaled by the donor's transfer weight from step 0. The predicted string is then *adapted* to the target before it is tested: its shape is reconciled with the target's own phonotactics and any regular alternations already learned (vowel harmony, final devoicing, epenthesis), so a single donor affix may project to a small family of surface variants. A prediction survives if one of its adapted forms actually occurs at the right edge (suffix) or left edge (prefix) of many different word types in the target text. For example, if a donor marks plural with `-at` and the table maps a → e, the system looks for a productive `-et` in the target, and for its harmony variants where the target has vowel harmony. Whole paradigms, not isolated affixes, are transferred together, so that the cells of a donor's case or tense table keep their mutual structure when they land on the target.

## 4 · Unsupervised induction

In parallel, Morfessor FlatCat [9] segments the target words into stems and affixes, and paradigm clustering [8] groups words that share a stem and differ by affix sets. This step sees only the target text, so it also finds morphology that the donors do not have, and it is the sole source of structure when the donor set is empty.

## 5 · Fitting and reconciliation

Transferred affixes are the prior, induced segmentation is the evidence; the prior's strength per affix is its transfer confidence from steps 0–3. A hypothesis is scored by how much it shortens the description of the corpus (minimum description length: the grammar plus the corpus encoded with it). Typological priors decide close calls: missing Grambank features of the target are imputed from its position in the tree (phylogenetically weighted nearest neighbours) [13], and implicational universals exclude improbable combinations — a transferred analysis that would violate a strong universal is overruled even when the donor supports it. A suffixing-preference prior applies where the evidence is balanced, because suffixing is cross-linguistically far more common than prefixing.

## 6 · Assembly

Accepted affixes and alternations are organised into paradigms and written as lingua-rules templates. The lemma convention (which form counts as the dictionary form: nominative singular, infinitive, third person singular…) is copied from the closest donor, because that is what grammars of the family use. Every rule records its origin (transferred from which donor, induced, or both), its confidence and the number of supporting word types. The grammar as a whole carries the same provenance upward: its `sources` list the donors it drew on and the induction step, its status is `provisional`, and its confidence aggregates the per-rule evidence. These fields are exactly what the output contract (section 9) returns under `grammar` and what each token's `rule` and `origin` point back into, so a provisional lemma is as traceable as a Tier A one.

## 7 · Validation and iteration

The grammar is judged on the target text itself: share of tokens that receive an analysis (coverage), description length, stability of the rules under bootstrap resampling of the text, and round-trip consistency (generate forms from lemmas and check that they occur). Weak rules are dropped or re-estimated and the loop repeats. The final grammar is stored as *provisional*; it becomes curated only after review.

    # Tier C: derive a provisional grammar for unknown language U
    def generate_grammar(U_text, donors, position):
        words = frequent_types(U_text, 2000)
        induced = morfessor_flatcat(U_text) + paradigm_clusters(U_text)
        priors  = impute_grambank(position) + universals()
        corr = init_correspondences()                                  # identity + common sound changes
        for it in range(MAX_ITER):
            pairs = [align_sca(w, lexicon[d]) for d in donors for w in words]
            pairs = [p for p in pairs if lexstat_score(p, corr) > TAU_ALIGN]
            corr  = estimate_correspondences(pairs, shuffled_baseline=True)    # EM step
            transferred = [map_affix(a, corr) for d in donors for a in affixes(d)]
            transferred = [a for a in transferred if edge_support(a, U_text) >= MIN_TYPES]
            grammar = fit_mdl(prior=transferred, evidence=induced, typology=priors)
            score = validate(grammar, U_text)                          # coverage, MDL, bootstrap stability
            if score.gain < EPS:
                break
        grammar.lemma_convention = lemma_convention(closest(donors))
        return grammar.with_status("provisional", provenance=donors, confidence=score)
