# Memory

Placeholder for future long-term agent memory (e.g. summarizing older
conversation turns, or storing learned facts across conversations).

Not implemented in this version: conversation history is passed to the
agent per-request by the Django layer (see `apps/conversations`), which is
sufficient for the current scope. This directory is kept so that a future
memory backend (vector store, summarizer, etc.) has an obvious home without
requiring changes to `agent.py`'s public interface.
