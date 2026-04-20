# Personal Data Analysis Assistant

> An AI-powered analysis assistant with a human-in-the-loop workflow — upload a dataset, interrogate it in plain English, approve an analysis plan, and receive a polished PowerPoint report.

![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-ff4b4b?style=flat-square)
![Claude API](https://img.shields.io/badge/Claude%20API-Anthropic-d97757?style=flat-square)
![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Overview

This tool is a multi-step, agentic data analysis assistant built with **OpenAI**. It follows an orchestrator-worker agent architecture inspired by Anthropic's *Building Effective Agents* framework — decomposing analytical questions into discrete, approvable steps, executing them with tool-use loops, and synthesising results into a shareable PowerPoint report.

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

### 7. Export to PDF
The assistant compiles findings, charts, narrative summaries, and your annotations into a structured `.pdf` report.

---

## Architecture

The assistant uses an **orchestrator-worker** pattern. A high-level orchestrator model handles planning, question decomposition, and ambiguity resolution. Worker agents receive bounded subtasks and use tools in a loop until each step is complete. This separation keeps individual model calls focused and auditable.

Built following Anthropic's **Building Effective Agents** framework: tool-calling loops, explicit state management, and minimal, composable agent roles.



---

*Personal Data Analysis Assistant · MIT Licence · Built with Claude & Streamlit*
