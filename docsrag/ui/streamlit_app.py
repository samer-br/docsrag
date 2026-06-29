"""Minimal Streamlit chat UI for DocsRAG.

Talks to the pipeline in-process so you can demo without running the API.
Run with:  streamlit run ui/streamlit_app.py
"""
from __future__ import annotations

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag import RagEngine          # noqa: E402
from app.store import VectorStore      # noqa: E402
from app.config import get_settings    # noqa: E402

st.set_page_config(page_title="DocsRAG", page_icon="📄")
st.title("📄 DocsRAG")
st.caption("Grounded answers over your documents, with citations.")


@st.cache_resource
def _engine() -> RagEngine | None:
    index_dir = get_settings().index_dir
    if not VectorStore.exists(index_dir):
        return None
    return RagEngine.load(index_dir)


engine = _engine()
if engine is None:
    st.warning("No index found. Run `python -m app.ingest` first, then reload.")
    st.stop()

with st.sidebar:
    st.header("Settings")
    top_k = st.slider("Top-k chunks", 1, 10, get_settings().top_k)
    use_graph = st.toggle("Graph retrieval", value=get_settings().use_graph_retrieval)
    st.markdown("**Try asking:**")
    for q in ["How long does the Atlas-7 battery last?",
              "What does it take to deploy to production?",
              "How do engineers authenticate to production?"]:
        st.markdown(f"- {q}")

question = st.chat_input("Ask a question about the documents…")
if question:
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        with st.spinner("Retrieving and answering…"):
            res = engine.answer(question, top_k=top_k, use_graph=use_graph)
        st.write(res.answer)
        st.caption(f"⏱ {res.latency_ms} ms")
        with st.expander("Sources"):
            for c in res.citations:
                label = c.source + (f" › {c.heading}" if c.heading else "")
                st.markdown(f"- **{label}** · score {c.score}")
