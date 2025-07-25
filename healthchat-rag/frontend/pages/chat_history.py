import streamlit as st
from datetime import datetime, timedelta
from components.chat_analytics import chat_analytics

st.set_page_config(page_title="Chat History | HealthChat RAG", page_icon="💬")
st.title("Chat History")

# Search and Filter Section
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search_query = st.text_input("Search conversations", placeholder="Enter keywords...")
with col2:
    date_filter = st.selectbox("Date Range", ["All Time", "Last 7 days", "Last 30 days", "Last 3 months"])
with col3:
    sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Duration", "Topic"])

# Chat Sessions Table
st.markdown("### Recent Conversations")
chat_sessions = [
    {
        "id": 1,
        "date": datetime.now() - timedelta(hours=2),
        "topic": "Blood pressure concerns",
        "summary": "Discussed high blood pressure readings and lifestyle changes",
        "duration": "15 minutes",
        "messages": 8
    },
    {
        "id": 2,
        "date": datetime.now() - timedelta(days=1),
        "topic": "Medication side effects",
        "summary": "Experiencing dizziness with new medication",
        "duration": "12 minutes",
        "messages": 6
    },
    {
        "id": 3,
        "date": datetime.now() - timedelta(days=3),
        "topic": "Diet recommendations",
        "summary": "Asked about diabetes-friendly meal planning",
        "duration": "20 minutes",
        "messages": 10
    }
]

# Display chat sessions
for session in chat_sessions:
    with st.expander(f"💬 {session['topic']} - {session['date'].strftime('%Y-%m-%d %H:%M')}"):
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(f"**Summary:** {session['summary']}")
            st.write(f"**Duration:** {session['duration']} | **Messages:** {session['messages']}")
        with col2:
            if st.button(f"View {session['id']}"):
                st.session_state.selected_session = session['id']
        with col3:
            if st.button(f"Export {session['id']}"):
                st.success(f"(Demo) Exporting conversation {session['id']}")
        with col4:
            if st.button(f"Delete {session['id']}"):
                st.warning(f"(Demo) Delete conversation {session['id']}")

# Chat Session Details View (placeholder)
if st.session_state.get('selected_session'):
    st.markdown("---")
    st.markdown("### Conversation Details")
    
    # Session Statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Messages", "8")
    with col2:
        st.metric("Duration", "15 minutes")
    with col3:
        st.metric("Topics Discussed", "3")
    with col4:
        st.metric("AI Responses", "4")
    
    # Key Topics
    st.markdown("**Key Topics Discussed:**")
    topics = ["Blood pressure management", "Lifestyle changes", "Medication adherence"]
    for topic in topics:
        st.write(f"• {topic}")
    
    # Conversation Messages
    st.markdown("**Conversation:**")
    messages = [
        {"sender": "user", "content": "I've been experiencing high blood pressure readings lately", "time": "14:30"},
        {"sender": "ai", "content": "I understand your concern. What are your typical readings?", "time": "14:31"},
        {"sender": "user", "content": "Around 140/90, sometimes higher", "time": "14:32"},
        {"sender": "ai", "content": "That's elevated. Let's discuss lifestyle changes that can help.", "time": "14:33"}
    ]
    
    for msg in messages:
        if msg["sender"] == "user":
            st.markdown(f"""
            <div style='background: #e3f2fd; padding: 10px; border-radius: 10px; margin: 5px 0; text-align: right;'>
                <div style='font-weight: bold;'>You ({msg['time']})</div>
                <div>{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='background: #f5f5f5; padding: 10px; border-radius: 10px; margin: 5px 0;'>
                <div style='font-weight: bold;'>AI Assistant ({msg['time']})</div>
                <div>{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Follow-up Recommendations
    st.markdown("**Follow-up Recommendations:**")
    recommendations = [
        "Monitor blood pressure daily for the next week",
        "Schedule a follow-up with your doctor",
        "Consider reducing salt intake"
    ]
    for rec in recommendations:
        st.write(f"• {rec}")
    
    # Export Options
    st.markdown("**Export Options:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Export as PDF"):
            st.success("(Demo) PDF export initiated")
    with col2:
        if st.button("Export as CSV"):
            st.success("(Demo) CSV export initiated")
    with col3:
        if st.button("Share Report"):
            st.success("(Demo) Sharing options opened")
    
    if st.button("Back to List"):
        st.session_state.selected_session = None

# Chat Analytics Section
st.markdown("---")
chat_analytics() 