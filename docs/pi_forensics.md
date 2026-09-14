# RichardLab π Forensics

A controlled experiment for testing whether predetermined encodings of a
birth date and name occur in a finite prefix of π.

## Scientific rule

The encoding matrix is fixed before searching. Results are recorded exactly.
Do not add new encodings after seeing an interesting hit and then treat the
new search as confirmatory evidence.

This experiment is exploratory. A hit does not imply that π "knows" the
person. Under a random-digit model, finite strings are expected to recur.

## Data source

The companion `pi-200m` project computes 200,000,000 fractional digits and
stores them in chunk files. RichardLab's searcher is compatible with that
layout.

## Build the corpus

From the `pi-200m` project:

```bash
python -m pip install -r requirements.txt
python scripts/pi_compute.py --digits 200000000 \
  --chunk-size 1000000 \
  --output-dir data/pi_digits
```

Do not commit generated digit files to Git.

## Run RichardLab

From the RichardLab root:

```bash
./.venv/bin/python -m ai.pi_forensics.cli \
  --pi-dir /path/to/pi-200m/data/pi_digits \
  --birthday 01211981 \
  --first-name RICHARD \
  --last-name SPRAGUE \
  --out pi_forensics_results.json
```

Run tests:

```bash
./.venv/bin/python -m pytest ai/tests/test_pi_forensics.py -q
```

## Interpretation

For a specific n-digit sequence, the simple iid uniform-digit model gives an
expected waiting scale of about 10^n positions.

The experiment reports an approximate probability of seeing the sequence by
the observed position. This is a model diagnostic, not a proof that π is
random or normal.

The most important control is the number of hypotheses tested. If many
encodings are searched, the chance that at least one produces an apparently
"surprising" early hit increases. Future versions should therefore add a
multiple-testing summary before making strong claims.
