import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'components')))
import breadcrumb

def test_breadcrumb_trail_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    breadcrumb.breadcrumb_trail(["Dashboard", "Profile", "Edit"])

def test_breadcrumb_trail_with_on_click(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    breadcrumb.breadcrumb_trail(["Dashboard", "Profile"], on_click=lambda: None) 