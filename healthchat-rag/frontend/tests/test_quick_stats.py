import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'components')))
import quick_stats

def test_quick_stats_cards_runs(monkeypatch):
    monkeypatch.setattr('streamlit.columns', lambda n: [type('DummyCol', (), {'__enter__': lambda s: None, '__exit__': lambda s, t, v, tb: None})() for _ in range(len(n) if isinstance(n, list) else n)])
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    quick_stats.quick_stats_cards() 