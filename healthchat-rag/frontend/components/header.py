import streamlit as st

# Dashboard Header Component
def dashboard_header(user_name="User", notifications=0):
    st.markdown("""
    <div style='display: flex; align-items: center; justify-content: space-between; padding: 1rem 0;'>
        <div style='display: flex; align-items: center;'>
            <span style='font-size: 2rem; margin-right: 1rem;'>🏥</span>
            <span style='font-size: 1.5rem; font-weight: bold;'>HealthChat RAG</span>
        </div>
        <div style='display: flex; align-items: center; gap: 1.5rem;'>
            <input type='text' placeholder='Search...' style='padding: 0.5rem; border-radius: 6px; border: 1px solid #ccc;'/>
            <span style='position: relative; font-size: 1.5rem;'>🔔<span style='position: absolute; top: -8px; right: -8px; background: #e76f51; color: #fff; border-radius: 50%; padding: 2px 6px; font-size: 0.8rem;'>""" + str(notifications) + """</span></span>
            <span style='font-size: 1.5rem; cursor: pointer;'>🌓</span>
            <div style='display: inline-block; position: relative;'>
                <span style='font-size: 1.5rem; cursor: pointer;'>👤</span>
                <span style='margin-left: 0.5rem;'>""" + user_name + """</span>
            </div>
        </div>
    </div>
    <hr style='margin: 0.5rem 0 1rem 0;'/>
    """, unsafe_allow_html=True) 