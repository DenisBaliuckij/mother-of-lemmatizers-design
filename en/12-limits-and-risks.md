# Limits and risks

- **Close relatives confuse recognition.** Mutually intelligible varieties (e.g. Bosnian/Croatian/Serbian, Malay/Indonesian) are routinely confused by LID; the outlier test and the second vote reduce but do not remove this.
- **Correspondences need data.** Reliable correspondence learning needs on the order of a hundred or more cognate pairs; very short texts only support n-gram and typological signals.
- **Loanwords and contact.** Borrowed vocabulary can make a language look related to its neighbour; LexStat's regularity test and the typological signal counter this but not completely.
- **Isolates and deep families.** Without close relatives, Tier C degrades to unsupervised induction plus priors. The SIGMORPHON 2020 shared task found unsupervised paradigm completion still largely unsolved, so expectations for isolates must be modest.
- **Orthography is not phonology.** Correspondences are learned over sounds; deep or inconsistent orthographies need a grapheme-to-phoneme step, which may itself be unavailable.
- **Provisional grammars can be wrong with confidence.** Every inferred lemma carries its origin and confidence, and downstream users should filter by status.
