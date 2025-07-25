import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'components')))
import metrics_summary

def test_metrics_summary_cards_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.columns', lambda n: [type('DummyCol', (), {'__enter__': lambda s: None, '__exit__': lambda s, t, v, tb: None})() for _ in range(n)])
    monkeypatch.setattr('streamlit.warning', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.info', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.metric', lambda *a, **k: None)
    metrics_summary.metrics_summary_cards() 