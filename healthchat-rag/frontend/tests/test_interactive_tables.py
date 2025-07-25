import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'components')))
import interactive_tables

# Sample DataFrame for testing
def sample_df():
    return pd.DataFrame({
        'id': [1, 2],
        'name': ['Alice', 'Bob'],
        'age': [30, 40],
        'blood_pressure': ['120/80', '130/85'],
        'weight': [65.0, 80.5],
        'last_visit': ['2024-06-01', '2024-06-15'],
        'status': ['Active', 'Inactive'],
        'medications': [1, 2]
    })

def test_generate_sample_data():
    df = interactive_tables.generate_sample_data()
    assert not df.empty
    assert set(['id', 'name', 'age', 'blood_pressure', 'weight', 'last_visit', 'status', 'medications']).issubset(df.columns)

def test_sortable_table_runs(monkeypatch):
    df = sample_df()
    # Patch st.selectbox to always return the first column and 'Ascending'
    monkeypatch.setattr('streamlit.selectbox', lambda *a, **k: df.columns[0] if 'Sort by' in a[0] else 'Ascending')
    # Patch st.dataframe and st.info to do nothing
    monkeypatch.setattr('streamlit.dataframe', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.info', lambda *a, **k: None)
    interactive_tables.sortable_table(df)

def test_paginated_table_runs(monkeypatch):
    df = sample_df()
    monkeypatch.setattr('streamlit.selectbox', lambda *a, **k: 1)
    monkeypatch.setattr('streamlit.dataframe', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.write', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.button', lambda *a, **k: False)
    interactive_tables.paginated_table(df)

def test_selectable_table_runs(monkeypatch):
    df = sample_df()
    monkeypatch.setattr('streamlit.multiselect', lambda *a, **k: [])
    monkeypatch.setattr('streamlit.dataframe', lambda *a, **k: None)
    interactive_tables.selectable_table(df)

def test_filterable_table_runs(monkeypatch):
    df = sample_df()
    monkeypatch.setattr('streamlit.multiselect', lambda *a, **k: df['status'].unique().tolist())
    monkeypatch.setattr('streamlit.slider', lambda *a, **k: (30, 40))
    monkeypatch.setattr('streamlit.date_input', lambda *a, **k: ('2024-06-01', '2024-06-15'))
    monkeypatch.setattr('streamlit.text_input', lambda *a, **k: '')
    monkeypatch.setattr('streamlit.dataframe', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.write', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.info', lambda *a, **k: None)
    interactive_tables.filterable_table(df)

def test_advanced_interactive_table_runs(monkeypatch):
    # Only test that it runs without error for the 'Sortable' table type
    df = sample_df()
    monkeypatch.setattr('streamlit.selectbox', lambda *a, **k: 'Sortable' if 'Table Type' in a[0] else df.columns[0])
    monkeypatch.setattr('streamlit.dataframe', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.info', lambda *a, **k: None)
    monkeypatch.setattr('streamlit.write', lambda *a, **k: None)
    interactive_tables.advanced_interactive_table() 