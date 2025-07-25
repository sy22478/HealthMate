import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'components')))
import activity_feed

def test_activity_feed_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.expander', lambda *a, **k: type('DummyExpander', (), {'__enter__': lambda s: None, '__exit__': lambda s, t, v, tb: None})())
    monkeypatch.setattr('streamlit.write', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.button', lambda *a, **k: False)
    activity_feed.activity_feed() 