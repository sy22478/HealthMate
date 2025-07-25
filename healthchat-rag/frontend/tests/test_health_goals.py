import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'components')))
import health_goals

def test_health_goals_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.expander', lambda *a, **k: type('DummyExpander', (), {'__enter__': lambda s: None, '__exit__': lambda s, t, v, tb: None})())
    monkeypatch.setattr('streamlit.columns', lambda n: [type('DummyCol', (), {'__enter__': lambda s: None, '__exit__': lambda s, t, v, tb: None})() for _ in range(len(n) if isinstance(n, list) else n)])
    monkeypatch.setattr('streamlit.progress', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.write', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.button', lambda *a, **k: False)
    monkeypatch.setattr('streamlit.selectbox', lambda *a, **k: "Weight Loss/Gain")
    monkeypatch.setattr('streamlit.number_input', lambda *a, **k: 0.0)
    monkeypatch.setattr('streamlit.text_input', lambda *a, **k: "")
    monkeypatch.setattr('streamlit.date_input', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.text_area', lambda *a, **k: "")
    monkeypatch.setattr('streamlit.success', lambda *a, **k: None)
    health_goals.health_goals() 