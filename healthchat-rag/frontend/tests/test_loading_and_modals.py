import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'components')))
import loading_and_modals

def test_loading_spinner_runs(monkeypatch):
    monkeypatch.setattr('streamlit.spinner', lambda *a, **k: __import__('contextlib').contextmanager(lambda: (yield))())
    loading_and_modals.loading_spinner("Testing...")

def test_skeleton_loading_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    loading_and_modals.skeleton_loading()

def test_progress_bar_demo_runs(monkeypatch):
    monkeypatch.setattr('streamlit.progress', lambda *a, **k: type('Dummy', (), {'progress': lambda self, v: None})())
    loading_and_modals.progress_bar_demo()

def test_fade_in_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    loading_and_modals.fade_in("Fade content")

def test_slide_modal_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    loading_and_modals.slide_modal("Slide content")

def test_hover_card_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    loading_and_modals.hover_card("Hover content")

def test_modal_component_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    loading_and_modals.modal_component("Title", "Body", "info")

def test_confirmation_modal_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    loading_and_modals.confirmation_modal()

def test_form_input_modal_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    loading_and_modals.form_input_modal()

def test_preview_modal_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    loading_and_modals.preview_modal()

def test_help_modal_runs(monkeypatch):
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    loading_and_modals.help_modal() 