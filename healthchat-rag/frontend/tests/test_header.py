import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'components')))
import header

def test_dashboard_header_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    header.dashboard_header("Test User", 5)

def test_dashboard_header_default_params(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    header.dashboard_header() 