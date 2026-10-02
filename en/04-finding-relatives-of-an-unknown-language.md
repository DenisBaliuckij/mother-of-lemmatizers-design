# Finding relatives of an unknown language

For an unknown language the system needs a small set of *donor* languages whose grammars can be carried over, and an estimate of where the language sits in the Glottolog family tree. No single signal is reliable: shared vocabulary may be borrowed, and similar spelling may only reflect a shared orthographic tradition. The ranker therefore combines four independent signals, following the LangRank approach of learning which features predict successful transfer.

| Signal | How it is computed | What it captures |
|----|----|----|
| LID posterior | The rejected distribution from recognition, aggregated over all segments | Surface resemblance, cheap and immediately available |
| Character n-gram profile | Rank-order distance (Cavnar–Trenkle "out-of-place") and cosine distance of 1–5-gram profiles against reference corpora of candidate languages | Phonotactics and orthography |
| Lexical cognacy | The target's most frequent word types are aligned with candidate lexicons (SCA alignment); LexStat-style scoring rewards *recurrent* sound correspondences over chance similarity; share of likely cognates in core vocabulary | Genealogical relatedness; the strongest signal when enough text exists |
| Typological fingerprint | Features estimated from the raw text (mean morphs per word from unsupervised segmentation, prefix vs suffix share, reduplication rate, word-order cues from frequent function words) compared with Grambank/URIEL+ vectors | Structural similarity; useful when the relatives are distant or unknown |

A gradient-boosted ranker (as in LangRank) combines the signals with priors (script, geography of candidate languages, data size of each candidate's grammar) and returns ranked donors. Tree position is estimated as the lowest common ancestor in Glottolog of the top donors, weighted by their scores. When no donor passes the cognacy threshold, the language is treated as a potential isolate: Tier C then relies only on unsupervised induction and typological priors.

    # rank donor languages for an unknown language U
    def find_relatives(U_text, posterior, candidates):
        freq_types = most_frequent_types(U_text, n=2000)
        for L in candidates:                                  # pre-filtered by script, geography, posterior
            f_post  = posterior.get(L, 0)
            f_ngram = out_of_place(ngram_profile(U_text), profile[L])
            f_cog   = lexstat_cognate_share(freq_types, lexicon[L])   # recurrent correspondences only
            f_typo  = cosine(estimate_typology(U_text), grambank_vec[L])
            score[L] = ranker.predict([f_post, f_ngram, f_cog, f_typo, prior(L)])
        donors = top_k(score, k=5)
        position = weighted_lca(glottolog, donors, score)
        return donors, position, is_isolate(f_cog_max < TAU_COG)
