import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'components')))
import sidebar

def test_dashboard_sidebar_runs(monkeypatch):
    monkeypatch.setattr('streamlit.sidebar', type('DummySidebar', (), {'__enter__': lambda s: None, '__exit__': lambda s, t, v, tb: None})())
    monkeypatch.setattr('streamlit_option_menu.option_menu', lambda *a, **k: "Dashboard")
    monkeypatch.setattr('streamlit.button', lambda *a, **k: False)
    sidebar.dashboard_sidebar() 