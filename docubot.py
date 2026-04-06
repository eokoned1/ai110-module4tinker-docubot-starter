"""
Core DocuBot class responsible for:
- Loading documents from the docs/ folder
- Building a simple retrieval index (Phase 1)
- Retrieving relevant snippets (Phase 1)
- Supporting retrieval only answers
- Supporting RAG answers when paired with Gemini (Phase 2)
"""

import os
import glob

class DocuBot:
    def __init__(self, docs_folder="docs", llm_client=None):
        """
        docs_folder: directory containing project documentation files
        llm_client: optional Gemini client for LLM based answers
        """
        self.docs_folder = docs_folder
        self.llm_client = llm_client

        # Load documents into memory
        self.documents = self.load_documents()  # List of (filename, text)

        # Build a retrieval index (implemented in Phase 1)
        self.index = self.build_index(self.documents)

    # -----------------------------------------------------------
    # Document Loading
    # -----------------------------------------------------------

    def load_documents(self):
        """
        Loads all .md and .txt files inside docs_folder.
        Returns a list of tuples: (filename, text)
        """
        docs = []
        pattern = os.path.join(self.docs_folder, "*.*")
        for path in glob.glob(pattern):
            if path.endswith(".md") or path.endswith(".txt"):
                with open(path, "r", encoding="utf8") as f:
                    text = f.read()
                filename = os.path.basename(path)
                docs.append((filename, text))
        return docs

    # -----------------------------------------------------------
    # Index Construction (Phase 1)
    # -----------------------------------------------------------

    def build_index(self, documents):
        """
        Build an index mapping chunk keys to paragraph content.
        Splits each document into paragraphs for finer-grained retrieval.
        """
        index = {}
        for filename, content in documents:
            # Split into paragraphs instead of storing whole file
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            for i, paragraph in enumerate(paragraphs):
                key = f"{filename}::chunk{i}"
                index[key] = paragraph
        return index

    # -----------------------------------------------------------
    # Scoring and Retrieval (Phase 1)
    # -----------------------------------------------------------

    def score_document(self, query, text):
        """
        Score relevance by counting query words that appear in text.
        Filters out common English stopwords to avoid false matches.
        """
        stopwords = {"is", "the", "a", "an", "and", "or", "in", "at", "to", "for", "of", "with", "by", "from", "as", "on", "be", "that", "this", "what", "where", "when", "why", "how"}
        query_words = [w for w in query.lower().split() if w not in stopwords]
        text_lower = text.lower()
        score = sum(1 for word in query_words if word in text_lower)
        return score

    def retrieve(self, query, top_k=3):
        """
        Score all chunks and return top_k relevant snippets.
        Applies a guardrail: returns empty list if best score is 0.
        """
        scores = []
        for chunk_key, content in self.index.items():
            score = self.score_document(query, content)
            scores.append((score, chunk_key, content))
        scores.sort(reverse=True, key=lambda x: x[0])

        # Guardrail: if the best score is 0, nothing is relevant
        if not scores or scores[0][0] == 0:
            return []

        return [(chunk_key, content) for _, chunk_key, content in scores[:top_k]]

    # -----------------------------------------------------------
    # Answering Modes
    # -----------------------------------------------------------

    def answer_retrieval_only(self, query, top_k=3):
        """
        Phase 1 retrieval only mode.
        Returns raw snippets and filenames with no LLM involved.
        If retrieval returns nothing (guardrail triggered), refuses to answer.
        """
        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I don't have enough information to answer that question."

        formatted = []
        for chunk_key, text in snippets:
            formatted.append(f"[{chunk_key}]\n{text}\n")

        return "\n---\n".join(formatted)

    def answer_rag(self, query, top_k=3):
        """
        Phase 2 RAG mode.
        Uses student retrieval to select snippets, then asks Gemini
        to generate an answer using only those snippets.
        """
        if self.llm_client is None:
            raise RuntimeError(
                "RAG mode requires an LLM client. Provide a GeminiClient instance."
            )

        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        return self.llm_client.answer_from_snippets(query, snippets)

    # -----------------------------------------------------------
    # Bonus Helper: concatenated docs for naive generation mode
    # -----------------------------------------------------------

    def full_corpus_text(self):
        """
        Returns all documents concatenated into a single string.
        This is used in Phase 0 for naive 'generation only' baselines.
        """
        return "\n\n".join(text for _, text in self.documents)
