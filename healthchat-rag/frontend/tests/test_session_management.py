import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'components')))
import session_management

def test_session_timeout_warning_runs(monkeypatch):
    monkeypatch.setattr('streamlit.sidebar', type('DummySidebar', (), {'__enter__': lambda s: None, '__exit__': lambda s, t, v, tb: None})())
    monkeypatch.setattr('streamlit.warning', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.button', lambda *a, **k: False)
    monkeypatch.setattr('streamlit.error', lambda *a, **k: None)
    monkeypatch.setattr('time.sleep', lambda *a, **k: None)
    session_management.session_timeout_warning()

def test_logout_confirmation_runs(monkeypatch):
    monkeypatch.setattr('streamlit.button', lambda *a, **k: False)
    monkeypatch.setattr('streamlit.warning', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.success', lambda *a, **k: None)
    session_management.logout_confirmation() 