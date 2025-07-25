import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'components')))
import main_content

def test_main_content_container_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    main_content.main_content_container()

def test_grid_row_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    main_content.grid_row("col1", "col2", "col3")

def test_show_loading_runs(monkeypatch):
    monkeypatch.setattr('streamlit.spinner', lambda *a, **k: __import__('contextlib').contextmanager(lambda: (yield))())
    monkeypatch.setattr('streamlit.write', lambda *a, **k: None)
    main_content.show_loading() 