## 数学形式化近一周追踪

当目标是“近一周尽量多拿到数学形式化相关论文”，而不是一次性精确命中单篇论文时，加载这个子模块。

这个指南默认“先高召回，再分层收缩”。同目录下的 `scripts/collect_math_formalization_weekly.py` 把这套流程固化成了可重复执行的脚本。

### 什么时候读这个子模块

- 用户明确要“近一周”论文。
- 用户想持续跟踪 Lean / Coq / Isabelle / Mathlib / theorem proving 相关方向。
- `daily -p math-formalization-weekly` 结果太少，甚至为空。
- `search -p math-formalization-weekly` 噪声太大，需要继续拆分检索入口。

### 检索阶梯

按顺序跑，不要指望一个 query 同时兼顾召回和精度。

#### 1. 核心 ITP / proof assistant 扫描

这是最稳的起点，精度相对高：

```bash
chattool explore arxiv search \
  'cat:cs.LO AND (all:"interactive theorem proving" OR all:"proof assistant" OR all:"theorem proving")' \
  --sort submittedDate -n 25 -v
```

截至 2026-03-19，观察到 2026-03-12 至 2026-03-18 这段时间的代表性命中：

- `2603.17457` Synthetic Differential Geometry in Lean
- `2603.15770` Formalization of QFT
- `2603.14663` Formalizing the Classical Isoperimetric Inequality in the Two-Dimensional Case
- `2603.12744` TaoBench: Do Automated Theorem Prover LLMs Generalize Beyond MathLib?

#### 2. Lean / Mathlib 形式化案例

当你想找“已经落到具体机器证明案例”的论文时，用这一组：

```bash
chattool explore arxiv search \
  '(abs:lean OR abs:coq OR abs:isabelle OR abs:metamath OR abs:mathlib) AND (abs:proof OR abs:formal)' \
  --sort submittedDate -n 25 -v
```

这一组在近一周里抓到了不少高价值论文：

- `2603.15929` Semi-Autonomous Formalization of the Vlasov-Maxwell-Landau Equilibrium
- `2603.15770` Formalization of QFT
- `2603.14663` Formalizing the Classical Isoperimetric Inequality in the Two-Dimensional Case
- `2603.14038` Machine-Verifying Toom-Cook Multiplication with Integer Evaluation Points
- `2603.12349` Budget-Sensitive Discovery Scoring: A Formally Verified Framework for Evaluating AI-Guided Scientific Selection
- `2603.12183` Proof-Carrying Materials: Falsifiable Safety Certificates for Machine-Learned Interatomic Potentials

#### 3. Auto-formalization / LLM 流水线

这一组用于盯“自然语言到形式证明/程序”的方向：

```bash
chattool explore arxiv search \
  '(cat:cs.AI OR cat:cs.CL OR cat:cs.LO) AND (all:autoformalization OR all:"auto-formalization" OR all:"informal-to-formal")' \
  --sort submittedDate -n 25 -v
```

近一周里最值得保留的命中：

- `2603.17233` Draft-and-Prune: Improving the Reliability of Auto-formalization for Logical Reasoning

这一组命中数通常不会很多，但密度高，不能省。

#### 4. ATP / benchmark / 泛化评测

不是所有相关论文都直接写成“某个数学命题形式化”，还有一批会落在 ATP 评测与泛化：

```bash
chattool explore arxiv search \
  '(cat:cs.AI OR cat:cs.LG OR cat:cs.LO) AND (all:"automated theorem prover" OR all:mathlib OR all:miniF2F OR all:ProofNet)' \
  --sort submittedDate -n 25 -v
```

近一周里较强的命中：

- `2603.12744` TaoBench: Do Automated Theorem Prover LLMs Generalize Beyond MathLib?

#### 5. 边界类补扫

这一步放在最后。它抓的是“和数学形式化相邻，但不一定是纯正主线”的论文。

重点盯这些关键词组合：

- formally verified evaluation metric
- proof-carrying safety certificate
- machine-verified algorithm
- 使用 Lean 4 等证明助手的领域形式化

同一周里值得保留的边界类例子：

- `2603.12349` Budget-Sensitive Discovery Scoring
- `2603.12183` Proof-Carrying Materials

### 噪声控制

下面这些词单独用时，通常会把噪声迅速拉高：

- `formalization`
- `formal`
- `proof`
- `verification`
- 单独的 `math.LO`

已经观察到的典型串味方向：

- 软件或机器人 specification
- legal reasoning formalization
- 泛 formal verification，但和数学形式化主线不直接相关

例如，过宽的 `abs:formalization` 会混进这些结果：

- `2603.17969` Specification-Aware Distribution Shaping for Robotics Foundation Models
- `2603.17150` Intent Formalization: A Grand Challenge for Reliable Coding in the Age of AI Agents

建议在放宽之前先加一个“锚点词”：

- `lean`、`lean 4`、`mathlib`
- `theorem proving`、`proof assistant`
- `automated theorem prover`
- `autoformalization`、`auto-formalization`
- `formalization of`、`formalizing`

### 收集脚本

用附带脚本一次性跑多组 query，并自动去重：

```bash
python skills/arxiv-explore/scripts/collect_math_formalization_weekly.py --days 7 --per-query 20
```

常用变体：

```bash
python skills/arxiv-explore/scripts/collect_math_formalization_weekly.py --list-groups
python skills/arxiv-explore/scripts/collect_math_formalization_weekly.py --group itp-core --group lean-case-studies -v
python skills/arxiv-explore/scripts/collect_math_formalization_weekly.py --strict
```

推荐使用方式：

1. 先不加 `--strict`，把近一周候选池尽量做厚。
2. 噪声上来以后，再加 `--strict` 做第二轮筛。
3. 一旦出现明确系统名或具体论文，立刻切到 `get <ARXIV_ID>`。

### 近一周样本池

这是 2026-03-19 调研时保留下来的代表性论文：

- `2603.17233` Draft-and-Prune: Improving the Reliability of Auto-formalization for Logical Reasoning
- `2603.17457` Synthetic Differential Geometry in Lean
- `2603.15929` Semi-Autonomous Formalization of the Vlasov-Maxwell-Landau Equilibrium
- `2603.15770` Formalization of QFT
- `2603.14663` Formalizing the Classical Isoperimetric Inequality in the Two-Dimensional Case
- `2603.14038` Machine-Verifying Toom-Cook Multiplication with Integer Evaluation Points
- `2603.12744` TaoBench: Do Automated Theorem Prover LLMs Generalize Beyond MathLib?
- `2603.12349` Budget-Sensitive Discovery Scoring: A Formally Verified Framework for Evaluating AI-Guided Scientific Selection
- `2603.12183` Proof-Carrying Materials: Falsifiable Safety Certificates for Machine-Learned Interatomic Potentials
