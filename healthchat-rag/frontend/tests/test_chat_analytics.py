import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'components')))
import chat_analytics

def test_chat_analytics_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.columns', lambda n: [type('DummyCol', (), {'__enter__': lambda s: None, '__exit__': lambda s, t, v, tb: None})() for _ in range(len(n) if isinstance(n, list) else n)])
    monkeypatch.setattr('streamlit.selectbox', lambda *a, **k: "Last 7 days")
    monkeypatch.setattr('streamlit.plotly_chart', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.write', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.progress', lambda *a, **k: None)
    chat_analytics.chat_analytics() 