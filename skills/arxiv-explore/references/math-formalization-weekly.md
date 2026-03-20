## Math Formalization Weekly

Use this guide when the goal is broad weekly collection for mathematical formalization research, not a single precise lookup.

This guide is intentionally recall-first: start broad, collect candidates, then narrow. The helper script in `scripts/collect_math_formalization_weekly.py` automates the same pattern.

### When To Load This Guide

- The user wants papers from the last 7 days.
- The user wants Lean / Coq / Isabelle / Mathlib / theorem proving papers as a rolling watchlist.
- The first `daily -p math-formalization-weekly` pass is empty or too sparse.
- The first `search -p math-formalization-weekly` pass is too noisy and needs structured follow-up queries.

### Query Ladder

Run the stages in order. Do not expect one query to do everything.

#### 1. Core ITP / proof assistant sweep

High precision starting point:

```bash
chattool explore arxiv search \
  'cat:cs.LO AND (all:"interactive theorem proving" OR all:"proof assistant" OR all:"theorem proving")' \
  --sort submittedDate -n 25 -v
```

Observed on March 19, 2026 for papers from March 12 to March 18, 2026:

- `2603.17457` Synthetic Differential Geometry in Lean
- `2603.15770` Formalization of QFT
- `2603.14663` Formalizing the Classical Isoperimetric Inequality in the Two-Dimensional Case
- `2603.12744` TaoBench: Do Automated Theorem Prover LLMs Generalize Beyond MathLib?

#### 2. Lean / Mathlib case studies

Use this when you want concrete machine-checked math or physics formalizations:

```bash
chattool explore arxiv search \
  '(abs:lean OR abs:coq OR abs:isabelle OR abs:metamath OR abs:mathlib) AND (abs:proof OR abs:formal)' \
  --sort submittedDate -n 25 -v
```

Observed strong hits:

- `2603.15929` Semi-Autonomous Formalization of the Vlasov-Maxwell-Landau Equilibrium
- `2603.15770` Formalization of QFT
- `2603.14663` Formalizing the Classical Isoperimetric Inequality in the Two-Dimensional Case
- `2603.14038` Machine-Verifying Toom-Cook Multiplication with Integer Evaluation Points
- `2603.12349` Budget-Sensitive Discovery Scoring: A Formally Verified Framework for Evaluating AI-Guided Scientific Selection
- `2603.12183` Proof-Carrying Materials: Falsifiable Safety Certificates for Machine-Learned Interatomic Potentials

#### 3. Auto-formalization / LLM pipeline tracking

Use this for informal-to-formal translation, solver program generation, or agentic proof workflows:

```bash
chattool explore arxiv search \
  '(cat:cs.AI OR cat:cs.CL OR cat:cs.LO) AND (all:autoformalization OR all:"auto-formalization" OR all:"informal-to-formal")' \
  --sort submittedDate -n 25 -v
```

Observed high-value hit:

- `2603.17233` Draft-and-Prune: Improving the Reliability of Auto-formalization for Logical Reasoning

This bucket is useful even when it returns only a few papers. The topic is sparse but important.

#### 4. ATP / benchmark / generalization

Use this to catch papers that are not direct formalization case studies but matter for theorem-prover evaluation:

```bash
chattool explore arxiv search \
  '(cat:cs.AI OR cat:cs.LG OR cat:cs.LO) AND (all:"automated theorem prover" OR all:mathlib OR all:miniF2F OR all:ProofNet)' \
  --sort submittedDate -n 25 -v
```

Observed strong hit:

- `2603.12744` TaoBench: Do Automated Theorem Prover LLMs Generalize Beyond MathLib?

#### 5. Boundary scan for adjacent formal methods

Use this only after the core passes above. It catches adjacent work that may still matter.

Look for:

- formally verified evaluation metrics
- proof-carrying safety certificates
- machine-verified algorithms
- domain formalization papers that use Lean 4 or similar proof assistants

Examples from the same week:

- `2603.12349` Budget-Sensitive Discovery Scoring
- `2603.12183` Proof-Carrying Materials

### Noise Control

These terms are usually too broad on their own:

- `formalization`
- `formal`
- `proof`
- `verification`
- `math.LO` by itself

Observed false-positive patterns:

- software or robotics specification papers
- legal reasoning formalization
- generic formal verification outside math formalization

Examples of noisy hits from broad `abs:formalization` searches:

- `2603.17969` Specification-Aware Distribution Shaping for Robotics Foundation Models
- `2603.17150` Intent Formalization: A Grand Challenge for Reliable Coding in the Age of AI Agents

Prefer adding one of these anchors before broadening:

- `lean`, `lean 4`, `mathlib`
- `theorem proving`, `proof assistant`
- `automated theorem prover`
- `autoformalization`, `auto-formalization`
- `formalization of`, `formalizing`

### Collector Script

Use the bundled script to run multiple weekly queries and deduplicate results:

```bash
python skills/arxiv-explore/scripts/collect_math_formalization_weekly.py --days 7 --per-query 20
```

Useful variants:

```bash
python skills/arxiv-explore/scripts/collect_math_formalization_weekly.py --list-groups
python skills/arxiv-explore/scripts/collect_math_formalization_weekly.py --group itp-core --group lean-case-studies -v
python skills/arxiv-explore/scripts/collect_math_formalization_weekly.py --strict
```

Recommended usage:

1. Start without `--strict` when building a broad weekly watchlist.
2. Add `--strict` when the result set becomes too noisy.
3. If a concrete system appears, pivot to a direct `get <ARXIV_ID>` read.

### Recent Example Set

These papers were concrete matches during collection on March 19, 2026:

- `2603.17233` Draft-and-Prune: Improving the Reliability of Auto-formalization for Logical Reasoning
- `2603.17457` Synthetic Differential Geometry in Lean
- `2603.15929` Semi-Autonomous Formalization of the Vlasov-Maxwell-Landau Equilibrium
- `2603.15770` Formalization of QFT
- `2603.14663` Formalizing the Classical Isoperimetric Inequality in the Two-Dimensional Case
- `2603.14038` Machine-Verifying Toom-Cook Multiplication with Integer Evaluation Points
- `2603.12744` TaoBench: Do Automated Theorem Prover LLMs Generalize Beyond MathLib?
- `2603.12349` Budget-Sensitive Discovery Scoring: A Formally Verified Framework for Evaluating AI-Guided Scientific Selection
- `2603.12183` Proof-Carrying Materials: Falsifiable Safety Certificates for Machine-Learned Interatomic Potentials
