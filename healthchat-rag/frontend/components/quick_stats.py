import streamlit as st

def quick_stats_cards():
    stats = [
        {"label": "Total Conversations", "value": 128, "icon": "💬", "trend": "up", "color": "#2a9d8f"},
        {"label": "Health Score", "value": 87, "icon": "❤️", "trend": "up", "color": "#e76f51"},
        {"label": "Last Check-up", "value": "2024-06-01", "icon": "🩺", "trend": "down", "color": "#e9c46a"},
        {"label": "Medications Count", "value": 3, "icon": "💊", "trend": "up", "color": "#264653"},
        {"label": "Upcoming Appointments", "value": 2, "icon": "📅", "trend": "neutral", "color": "#f4a261"},
    ]
    cols = st.columns(len(stats))
    for i, stat in enumerate(stats):
        with cols[i]:
            st.markdown(f"""
                <div class='card' style='background: {stat['color']}; color: #fff; border-radius: 8px; padding: 1.2rem; text-align: center; min-height: 120px;'>
                    <div style='font-size: 2rem;'>{stat['icon']}</div>
                    <div style='font-size: 2.2rem; font-weight: bold;'>{stat['value']}</div>
                    <div style='font-size: 1.1rem; margin-bottom: 0.2rem;'>{stat['label']}</div>
                    <div style='font-size: 1.2rem;'>
                        {('⬆️' if stat['trend']=='up' else ('⬇️' if stat['trend']=='down' else '➡️'))}
                    </div>
                </div>
            """, unsafe_allow_html=True) 