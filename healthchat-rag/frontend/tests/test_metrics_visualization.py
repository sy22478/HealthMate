import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'components')))
import metrics_visualization

def test_metrics_visualization_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.columns', lambda n: [type('DummyCol', (), {'__enter__': lambda s: None, '__exit__': lambda s, t, v, tb: None})() for _ in range(len(n) if isinstance(n, list) else n)])
    monkeypatch.setattr('streamlit.selectbox', lambda *a, **k: "Last 7 days")
    monkeypatch.setattr('streamlit.checkbox', lambda *a, **k: False)
    monkeypatch.setattr('streamlit.plotly_chart', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.button', lambda *a, **k: False)
    monkeypatch.setattr('streamlit.success', lambda *a, **k: None)
    metrics_visualization.metrics_visualization() 