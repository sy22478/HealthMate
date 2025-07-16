import streamlit as st
import requests
import json

API_URL = "http://localhost:8000/enhanced/enhanced_chat"
st.set_page_config(page_title="Diagnosis QA Dashboard", layout="wide")

# --- Test Cases ---
TEST_CASES = {
    "Classic Strep Throat": {
        "message": "I have a sore throat, fever, and swollen lymph nodes.",
        "chat_type": "diagnosis",
        "symptoms": ["sore throat", "fever", "swollen lymph nodes"]
    },
    "Possible Heart Attack": {
        "message": "Sudden chest pain, shortness of breath, and sweating.",
        "chat_type": "diagnosis",
        "symptoms": ["chest pain", "shortness of breath", "sweating"]
    },
    "Tick Bite and Rash": {
        "message": "I have joint pain, a rash, and a recent tick bite.",
        "chat_type": "diagnosis",
        "symptoms": ["joint pain", "rash", "tick bite"]
    },
    "Jaundice and Abdominal Pain": {
        "message": "I have abdominal pain, nausea, and yellowing of my eyes.",
        "chat_type": "diagnosis",
        "symptoms": ["abdominal pain", "nausea", "jaundice"]
    },
    "Outdoor Swelling (Your Example)": {
        "message": "After playing frisbee golf in the woods, I developed swelling and itchiness in my left calf. It got worse the next day, but improved after a hot water bath.",
        "chat_type": "diagnosis",
        "symptoms": ["left calf swelling", "itchiness", "recent outdoor exposure", "improved with hot water"]
    },
    "Ambiguous Fatigue": {
        "message": "I've been feeling tired, have a mild fever, and some muscle aches.",
        "chat_type": "diagnosis",
        "symptoms": ["fatigue", "mild fever", "muscle aches"]
    }
}

# --- Authentication ---
st.sidebar.header("Authentication")
auth_token = st.sidebar.text_input("Bearer Token (optional)", type="password")

# --- Test Case Selection ---
st.sidebar.header("Test Case")
case_name = st.sidebar.selectbox("Choose a test case", list(TEST_CASES.keys()))
payload = TEST_CASES[case_name]
st.sidebar.write("Payload:", payload)

# --- Custom Input ---
st.sidebar.header("Custom Test")
custom_message = st.sidebar.text_area("Custom message")
custom_symptoms = st.sidebar.text_area("Custom symptoms (comma-separated)")
if st.sidebar.button("Use Custom Input"):
    payload = {
        "message": custom_message,
        "chat_type": "diagnosis",
        "symptoms": [s.strip() for s in custom_symptoms.split(",") if s.strip()]
    }

# --- Main UI ---
st.title("Conversational Agent Diagnosis QA Dashboard")
st.write("Test and visualize your agent's responses. Results are categorized automatically.")

if st.button("Run Test"):
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        st.subheader("Raw API Response")
        st.json(response.json())
        data = response.json()
    except Exception as e:
        st.error(f"API call failed: {e}")
        st.stop()

    # --- Categorization ---
    diagnosis_results = data.get("diagnosis_results")
    response_text = data.get("response", "")
    emergency = any(
        (d.get("urgency", "").lower() == "emergency") for d in (diagnosis_results or [])
    )
    fallback = (
        not diagnosis_results
        or (isinstance(diagnosis_results, list) and len(diagnosis_results) == 0)
        or ("consult" in response_text.lower() and "provider" in response_text.lower())
    )

    # --- Display Sections ---
    if emergency:
        st.error("🚨 Emergency Detected in Diagnosis Results!")
    if diagnosis_results and not fallback:
        st.success("Differential Diagnosis Results")
        for i, diag in enumerate(diagnosis_results, 1):
            with st.expander(f"{i}. {diag.get('condition', 'Unknown')} (Confidence: {diag.get('confidence', 0):.0%})"):
                st.write("**Urgency:**", diag.get("urgency", "N/A"))
                st.write("**Reasoning:**", diag.get("reasoning", ""))
                st.write("**Supporting Symptoms:**", diag.get("supporting_symptoms", []))
                st.write("**Contradicting Symptoms:**", diag.get("contradicting_symptoms", []))
                st.write("**Next Questions:**", diag.get("next_questions", []))
                st.write("**Recommended Actions:**", diag.get("recommended_actions", []))
    elif fallback:
        st.warning("⚠️ Generic Fallback or No Diagnosis Results")
        st.write(response_text)
    else:
        st.info("Other/Uncategorized Response")
        st.write(response_text)

    # --- Show disclaimer if present ---
    if "disclaimer" in data:
        st.info(data["disclaimer"])

st.markdown("---")
st.markdown("**Tip:** Use the sidebar to select or enter test cases. Add your Bearer token if authentication is required.")