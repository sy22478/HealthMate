import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'components')))
import enhanced_chat

def test_simple_chat_interface_init():
    chat_interface = enhanced_chat.SimpleChatInterface()
    assert chat_interface.api_base_url == "http://localhost:8000"

def test_simple_chat_interface_setup_page(monkeypatch):
    monkeypatch.setattr('streamlit.set_page_config', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.title', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.markdown', lambda *a, **k: None)
    
    chat_interface = enhanced_chat.SimpleChatInterface()
    chat_interface.setup_page()

def test_simple_chat_interface_render_sidebar(monkeypatch):
    monkeypatch.setattr('streamlit.sidebar', type('DummySidebar', (), {'__enter__': lambda s: None, '__exit__': lambda s, t, v, tb: None})())
    monkeypatch.setattr('streamlit.header', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.number_input', lambda *a, **k: 30)
    monkeypatch.setattr('streamlit.selectbox', lambda *a, **k: "Male")
    monkeypatch.setattr('streamlit.text_area', lambda *a, **k: "")
    monkeypatch.setattr('streamlit.warning', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.subheader', lambda *a, **k: None)
    
    chat_interface = enhanced_chat.SimpleChatInterface()
    result = chat_interface.render_sidebar()
    assert isinstance(result, dict)
    assert 'age' in result
    assert 'gender' in result
    assert 'medical_conditions' in result 