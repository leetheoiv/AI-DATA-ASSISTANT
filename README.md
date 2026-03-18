# Personal Data Analysis Assistant

> An AI-powered analysis assistant with a human-in-the-loop workflow — upload a dataset, interrogate it in plain English, approve an analysis plan, and receive a polished PowerPoint report.

![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-ff4b4b?style=flat-square)
![Claude API](https://img.shields.io/badge/Claude%20API-Anthropic-d97757?style=flat-square)
![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Overview

This tool is a multi-step, agentic data analysis assistant built with **Streamlit** and the **Anthropic Claude API**. It follows an orchestrator-worker agent architecture inspired by Anthropic's *Building Effective Agents* framework — decomposing analytical questions into discrete, approvable steps, executing them with tool-use loops, and synthesising results into a shareable PowerPoint report.

**Human-in-the-loop by design.** Every analysis plan is surfaced for your review before any computation runs. You approve, modify, or remove steps — the model never acts unilaterally.

---

## Workflow

### 1. Upload your dataset
Upload a CSV or Excel file. The assistant immediately echoes the schema — column names, inferred types, row count, and a sample of values.

### 2. Automatic dataset profiling
Descriptive statistics are computed and displayed: distributions, null counts, unique value counts, and correlation hints — before you write a single prompt.

### 3. Provide dataset context
Tell the model what the data represents, who collected it, and what business questions matter. This context is injected into every subsequent prompt, grounding the model's reasoning in your domain.

### 4. Ask a question in plain English
Pose any analytical question. The model first decomposes it — surfacing ambiguities, clarifying scope, and confirming intent — before proceeding.

### 5. Review & approve the analysis plan ⬅ *human-in-the-loop*
The orchestrator produces a numbered list of analysis steps. You approve, edit, reorder, or delete individual steps before the model executes a single line of computation.

### 6. Tool-use execution loop
Worker agents execute each approved step using specialised tools — statistical computation, chart generation, and data transformation. Results stream back into the session.

### 7. Interpret and annotate visuals
For each chart produced, you can supply your own interpretation. These annotations are stored and included verbatim in the final report, preserving business context.

### 8. Export to PowerPoint
The assistant compiles findings, charts, narrative summaries, and your annotations into a structured `.pptx` report — ready to share with stakeholders.

---

## Architecture

The assistant uses an **orchestrator-worker** pattern. A high-level orchestrator model handles planning, question decomposition, and ambiguity resolution. Worker agents receive bounded subtasks and use tools in a loop until each step is complete. This separation keeps individual model calls focused and auditable.

Built following Anthropic's **Building Effective Agents** framework: tool-calling loops, explicit state management, and minimal, composable agent roles.

### Project Structure

```
├── app.py                      ← Streamlit entry point & session state
├── orchestrator/
│   ├── planner.py              ← question decomposition & plan generation
│   └── reviewer.py             ← human-in-the-loop step approval UI
├── workers/
│   ├── analyst.py              ← statistical analysis worker
│   ├── visualiser.py           ← chart generation worker
│   └── reporter.py             ← PowerPoint assembly
├── tools/
│   └── tool_definitions.py     ← all tool schemas (Anthropic format)
├── client/
│   └── spectrum_client.py      ← custom Anthropic API wrapper
└── requirements.txt
```

---

## Tech Stack

| Library | Role |
|---|---|
| `streamlit` | UI layer, session state, file uploads |
| `anthropic` | Claude API — orchestration & tool-calling |
| `pandas` | Dataset loading, profiling, transformation |
| `matplotlib` / `plotly` | Chart generation via tool-use |
| `python-pptx` | PowerPoint report assembly |
| `SpectrumClient` | Custom API client with retry & logging |

---

## Getting Started

### 1. Clone & install

```bash
git clone https://github.com/your-username/data-analysis-assistant.git
cd data-analysis-assistant

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure your API key

```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

> ⚠️ Never commit your `.env` file. It is listed in `.gitignore` by default.

### 3. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Usage Tips

- **Be specific with context.** The richer the dataset description you provide in step 3, the more grounded the model's analysis plan will be.
- **Treat the plan review seriously.** This is your primary lever for quality. Remove steps that aren't relevant; add specific metrics you care about.
- **Add interpretations before exporting.** The model's chart summaries are starting points — your domain knowledge makes the report useful to stakeholders.
- **Large datasets.** For files over ~50MB, consider sampling before upload to keep latency reasonable.

---

## Roadmap

- [ ] Checkpointing & session persistence (LangGraph / custom SQLite store)
- [ ] Streaming plan generation with live step-by-step reveal
- [ ] Multi-dataset joins and cross-file analysis
- [ ] Export to PDF and Tableau-ready `.hyper` extracts
- [ ] Memory of past sessions for iterative, longitudinal analysis

---

## Contributing

Pull requests are welcome. For significant changes, please open an issue first to discuss scope. All contributions should include updated docstrings and, where relevant, a brief note in the changelog.

```bash
ruff check .
black --check .
```

---

*Personal Data Analysis Assistant · MIT Licence · Built with Claude & Streamlit*
