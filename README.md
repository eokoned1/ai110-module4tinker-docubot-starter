# DocuBot

DocuBot is a small docs assistant built for comparing three QA styles side by side:

1. Naive LLM (just ask the model)
2. Retrieval only (no model, just return relevant snippets)
3. RAG (retrieve snippets, then generate an answer grounded in those snippets)

The project docs are plain markdown files in the `docs/` folder. There is no real backend here; this is a focused retrieval + prompting exercise.

## Why This Project Exists

This repo makes one thing very obvious: fluent answers are not always true answers.

- Mode 1 sounds smart, but can hallucinate.
- Mode 2 is honest and traceable, but can feel raw.
- Mode 3 is the goal: readable answers with evidence, plus refusal when evidence is weak.

## What Was Implemented

The retrieval pipeline in `docubot.py` now includes:

- Paragraph chunking (`filename::chunkN`) instead of whole-file scoring
- Simple keyword scoring with stopword filtering
- Top-k retrieval over chunks
- Guardrail behavior: if no meaningful match exists, return an explicit refusal

That means out-of-scope questions (for example, Kubernetes deployment) now fail safely instead of producing confident nonsense.

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set your environment variables in `.env`:

```env
GEMINI_API_KEY=your_api_key_here
```

You can still run Mode 2 without a Gemini key.

3. Run DocuBot:

```bash
python main.py
```

## Modes

- `1` Naive LLM: model answers directly (not grounded)
- `2` Retrieval only: returns top chunks only
- `3` RAG: uses retrieved chunks + LLM synthesis with refusal rules

## Example Observations

Question: "Where is the auth token generated?"

- Mode 1: can drift into generic auth platform explanations
- Mode 2: returns the most relevant chunks it found
- Mode 3: answers from retrieved context or refuses if evidence is insufficient

Question: "What is the deployment process for Kubernetes?"

- Mode 1: likely hallucinates
- Mode 2: guardrail refusal
- Mode 3: guardrail refusal

## Optional Evaluation

Run:

```bash
python evaluation.py
```

This prints simple retrieval hit-rate metrics over sample queries.

## Project Files

- `docubot.py`: retrieval/indexing/chunking logic
- `llm_client.py`: Gemini prompts and response handling
- `dataset.py`: sample queries and fallback docs
- `model_card.md`: reflection on behavior, tradeoffs, and safety

## Requirements

- Python 3.9+
- Gemini API key for Modes 1 and 3

## Submission Summary

The core concept in this activity was understanding that reliable QA systems come from retrieval quality and guardrails, not from fluent model output alone. Students are most likely to struggle with retrieval tuning, especially chunk size, keyword scoring choices, and why the "best" chunk can still miss the exact answer. AI was helpful for speeding up iteration, generating starter implementations, and suggesting debugging checks when comparing retrieval behavior across modes. AI was misleading when it sounded confident but introduced generic details that were not present in the project documentation. A key lesson is that Mode 3 RAG can still fail if Mode 2 retrieval surfaces weak evidence, so improving retrieval remains the highest leverage improvement. To guide a student without giving the answer, I would ask them to run the same query in all three modes, inspect the top returned chunks and scores, and explain which retrieval change would most improve grounding.
