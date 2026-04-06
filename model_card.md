# DocuBot Model Card

## What DocuBot Does
DocuBot is a retrieval-augmented assistant that answers developer questions 
about a software project's documentation. Rather than passing everything to 
an LLM and hoping for the best, it first searches a local docs folder for 
relevant chunks, then asks the LLM to answer using only those chunks as 
evidence. The result is a system that is grounded, honest about what it 
doesn't know, and far more reliable than naive generation.

## The Three Modes

### Mode 1: Naive LLM
The model receives the full documentation corpus and answers freely. On 
the surface the responses look great — well structured, confident, detailed. 
But when you check them against the actual docs, they fall apart. Asked 
"Where is the auth token generated?", it described Auth0, Okta, Keycloak, 
and AWS Cognito — none of which appear anywhere in the project. This is 
the hallucination problem in practice: fluent output that has no grounding 
in the actual source material.

### Mode 2: Retrieval Only
No LLM involved — just keyword scoring and chunk ranking. This mode never 
hallucinates because it never generates anything. It returns raw text 
snippets ranked by relevance. The guardrail works well here too: asking 
about Kubernetes deployment correctly returns "I don't have enough 
information to answer that question" because no chunks scored above zero. 
The tradeoff is that the output requires the user to interpret raw snippets 
rather than receiving a clean answer.

### Mode 3: RAG (Retrieval + LLM)
This is where the two approaches complement each other. Retrieval finds the 
most relevant chunks, and the LLM synthesizes a readable answer from only 
those chunks. When the retrieved context is strong, the answer is accurate 
and well-expressed. When retrieval comes up empty, the guardrail prevents 
the LLM from ever seeing an empty context — so it refuses cleanly instead 
of inventing something plausible-sounding.

## Observed Results

| Question | Mode 1 | Mode 2 | Mode 3 |
|----------|--------|--------|--------|
| "Where is the auth token generated?" | Hallucinated (Auth0, Okta, Keycloak) | Returned API endpoint chunks | Honest refusal — wrong chunks retrieved |
| "Kubernetes deployment process?" | Confident hallucination | Guardrail triggered correctly | Guardrail triggered correctly |

## Where RAG Still Falls Short
The biggest lesson from this activity is that RAG quality is bounded by 
retrieval quality. In Mode 3, when asked about auth token generation, the 
system returned chunks from API_REFERENCE.md instead of AUTH.md — and 
even though the LLM was well-constrained, it couldn't generate a correct 
answer from the wrong evidence. The actual answer ("Tokens are created by 
the generate_access_token function in auth_utils.py") was sitting in the 
docs the whole time, but the scoring function didn't rank that chunk highly 
enough. Better chunking strategies, phrase-weighted scoring, or semantic 
embeddings would close this gap.

## Design Decisions

**Chunking by paragraph** rather than whole documents made a significant 
difference. Whole-document scoring buries specific answers inside files 
that happen to mention the right words many times. Paragraph-level chunks 
let precise answers surface on their own.

**Stopword filtering in scoring** helped prioritize meaningful content 
words over common English articles and prepositions. Without it, queries 
like "What is the weather in Paris?" would match any docs containing "is" 
or "the", generating false positives.

**The guardrail is a feature, not a limitation.** A system that says 
"I don't know" when it lacks evidence is safer and more trustworthy than 
one that always produces an answer. This was most visible with the 
Kubernetes question — Mode 1 generated a detailed, confident, completely 
fabricated response while Modes 2 and 3 both refused cleanly.

## Key Takeaways
- Confident output is not the same as correct output
- Retrieval is the foundation of the system — the LLM can only be as 
  good as the context it receives
- Chunk granularity and scoring strategy are the two biggest levers 
  for improving retrieval quality
- Guardrails that produce honest refusals are a deliberate design 
  choice, not a failure state
