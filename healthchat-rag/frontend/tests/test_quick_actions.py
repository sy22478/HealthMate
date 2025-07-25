import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'components')))
import quick_actions

def test_quick_action_buttons_runs(monkeypatch):
    monkeypatch.setattr('streamlit.columns', lambda n: [type('DummyCol', (), {'__enter__': lambda s: None, '__exit__': lambda s, t, v, tb: None})() for _ in range(len(n) if isinstance(n, list) else n)])
    monkeypatch.setattr('streamlit.button', lambda *a, **k: False)
    monkeypatch.setattr('streamlit.spinner', lambda *a, **k: __import__('contextlib').contextmanager(lambda: (yield))())
    monkeypatch.setattr('streamlit.success', lambda *a, **k: None)
    quick_actions.quick_action_buttons() 