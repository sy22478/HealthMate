import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

# Sample data for demonstration
def generate_sample_data():
    data = []
    for i in range(50):
        data.append({
            'id': i + 1,
            'name': f'Patient {i + 1}',
            'age': random.randint(25, 80),
            'blood_pressure': f'{random.randint(110, 140)}/{random.randint(70, 90)}',
            'weight': round(random.uniform(50, 120), 1),
            'last_visit': (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d'),
            'status': random.choice(['Active', 'Inactive', 'Pending']),
            'medications': random.randint(0, 5)
        })
    return pd.DataFrame(data)

# Sortable Table Component
def sortable_table(df, sort_column=None, sort_direction='asc'):
    st.markdown("### Sortable Data Table")
    
    # Sort controls
    col1, col2 = st.columns([2, 1])
    with col1:
        sort_by = st.selectbox("Sort by", df.columns.tolist(), index=0)
    with col2:
        sort_dir = st.selectbox("Direction", ["Ascending", "Descending"])
    
    # Apply sorting
    if sort_dir == "Descending":
        df_sorted = df.sort_values(by=sort_by, ascending=False)
    else:
        df_sorted = df.sort_values(by=sort_by, ascending=True)
    
    # Display table with sorting indicators
    st.dataframe(df_sorted, use_container_width=True)
    
    # Sort status
    st.info(f"Sorted by: {sort_by} ({sort_dir.lower()})")

# Pagination Controls
def paginated_table(df, page_size=10):
    st.markdown("### Paginated Data Table")
    
    # Pagination controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        page_size = st.selectbox("Items per page", [5, 10, 20, 50], index=1)
    with col2:
        total_pages = (len(df) + page_size - 1) // page_size
        current_page = st.selectbox("Page", range(1, total_pages + 1), index=0)
    with col3:
        st.write(f"Total: {len(df)} items")
    
    # Calculate page data
    start_idx = (current_page - 1) * page_size
    end_idx = start_idx + page_size
    page_data = df.iloc[start_idx:end_idx]
    
    # Display paginated table
    st.dataframe(page_data, use_container_width=True)
    
    # Page navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("Previous") and current_page > 1:
            st.session_state.current_page = current_page - 1
    with col2:
        st.write(f"Page {current_page} of {total_pages}")
    with col3:
        if st.button("Next") and current_page < total_pages:
            st.session_state.current_page = current_page + 1

# Table with Row Selection
def selectable_table(df):
    st.markdown("### Table with Row Selection")
    
    # Row selection
    selected_rows = st.multiselect(
        "Select rows",
        options=df.index.tolist(),
        format_func=lambda x: f"Row {x + 1}: {df.iloc[x]['name']}"
    )
    
    # Display selected rows
    if selected_rows:
        selected_data = df.iloc[selected_rows]
        st.write(f"Selected {len(selected_rows)} rows:")
        st.dataframe(selected_data, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)
    
    # Bulk actions for selected rows
    if selected_rows:
        st.markdown("**Bulk Actions**")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Export Selected"):
                st.success(f"(Demo) Exported {len(selected_rows)} rows")
        with col2:
            if st.button("Delete Selected"):
                st.warning(f"(Demo) Deleted {len(selected_rows)} rows")
        with col3:
            if st.button("Update Selected"):
                st.info(f"(Demo) Updated {len(selected_rows)} rows")

# Table Filtering
def filterable_table(df):
    st.markdown("### Filterable Data Table")
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Status filter
        status_filter = st.multiselect(
            "Filter by Status",
            options=df['status'].unique().tolist(),
            default=df['status'].unique().tolist()
        )
    
    with col2:
        # Age range filter
        age_min, age_max = st.slider(
            "Age Range",
            min_value=int(df['age'].min()),
            max_value=int(df['age'].max()),
            value=(int(df['age'].min()), int(df['age'].max()))
        )
    
    with col3:
        # Date range filter
        date_col = 'last_visit'
        min_date = pd.to_datetime(df[date_col].min())
        max_date = pd.to_datetime(df[date_col].max())
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    if status_filter:
        filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
    
    filtered_df = filtered_df[
        (filtered_df['age'] >= age_min) & 
        (filtered_df['age'] <= age_max)
    ]
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df[date_col]) >= pd.to_datetime(start_date)) &
            (pd.to_datetime(filtered_df[date_col]) <= pd.to_datetime(end_date))
        ]
    
    # Search within table
    search_term = st.text_input("Search in table", placeholder="Enter search term...")
    if search_term:
        mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
        filtered_df = filtered_df[mask]
    
    # Display filtered results
    st.write(f"Showing {len(filtered_df)} of {len(df)} records")
    st.dataframe(filtered_df, use_container_width=True)
    
    # Filter summary
    if len(filtered_df) < len(df):
        st.info(f"Applied filters: Status={status_filter}, Age={age_min}-{age_max}, Date Range={date_range}, Search='{search_term}'")

# Advanced Table with All Features
def advanced_interactive_table():
    st.markdown("### Advanced Interactive Table")
    
    # Generate sample data
    df = generate_sample_data()
    
    # Table configuration
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("**Table Features:**")
        st.write("• Sortable columns")
        st.write("• Pagination")
        st.write("• Row selection")
        st.write("• Column filtering")
        st.write("• Search functionality")
        st.write("• Bulk actions")
    with col2:
        table_type = st.selectbox(
            "Table Type",
            ["Sortable", "Paginated", "Selectable", "Filterable", "All Features"]
        )
    
    # Display appropriate table type
    if table_type == "Sortable":
        sortable_table(df)
    elif table_type == "Paginated":
        paginated_table(df)
    elif table_type == "Selectable":
        selectable_table(df)
    elif table_type == "Filterable":
        filterable_table(df)
    else:  # All Features
        st.markdown("**Combined Interactive Table**")
        
        # Filter section
        with st.expander("Filters", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.multiselect("Status", df['status'].unique())
                age_range = st.slider("Age Range", int(df['age'].min()), int(df['age'].max()), (25, 80))
            with col2:
                search_term = st.text_input("Search", placeholder="Search in all columns...")
                sort_by = st.selectbox("Sort by", df.columns.tolist())
        
        # Apply filters
        filtered_df = df.copy()
        if status_filter:
            filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
        filtered_df = filtered_df[
            (filtered_df['age'] >= age_range[0]) & 
            (filtered_df['age'] <= age_range[1])
        ]
        if search_term:
            mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
            filtered_df = filtered_df[mask]
        
        # Sort
        filtered_df = filtered_df.sort_values(by=sort_by)
        
        # Pagination
        page_size = st.selectbox("Items per page", [5, 10, 20], index=1)
        total_pages = max(1, (len(filtered_df) + page_size - 1) // page_size)
        current_page = st.selectbox("Page", range(1, total_pages + 1), index=0)
        
        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        page_data = filtered_df.iloc[start_idx:end_idx]
        
        # Row selection
        selected_indices = st.multiselect(
            "Select rows",
            options=page_data.index.tolist(),
            format_func=lambda x: f"Row {x + 1}: {page_data.loc[x, 'name']}"
        )
        
        # Display table
        st.dataframe(page_data, use_container_width=True)
        
        # Bulk actions
        if selected_indices:
            st.markdown("**Bulk Actions for Selected Rows**")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Export Selected"):
                    st.success(f"(Demo) Exported {len(selected_indices)} rows")
            with col2:
                if st.button("Delete Selected"):
                    st.warning(f"(Demo) Deleted {len(selected_indices)} rows")
            with col3:
                if st.button("Update Selected"):
                    st.info(f"(Demo) Updated {len(selected_indices)} rows")
        
        # Summary
        st.info(f"Showing {len(page_data)} of {len(filtered_df)} filtered records (Page {current_page} of {total_pages})") 