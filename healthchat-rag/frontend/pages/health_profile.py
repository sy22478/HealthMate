import streamlit as st
from datetime import date

def calculate_bmi(weight, height):
    if height > 0:
        return round(weight / ((height / 100) ** 2), 1)
    return 0

st.set_page_config(page_title="Health Profile | HealthChat RAG", page_icon="🩺")
st.title("Health Profile")

# Personal Information Section
with st.expander("Personal Information", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        full_name = st.text_input("Full Name", value="Jane Doe")
        birth_date = st.date_input("Birth Date", value=date(1990, 1, 1))
        gender = st.selectbox("Gender", ["Female", "Male", "Other", "Prefer not to say"])
    with col2:
        height = st.number_input("Height (cm)", min_value=50, max_value=250, value=170)
        weight = st.number_input("Weight (kg)", min_value=20, max_value=200, value=65)
        bmi = calculate_bmi(weight, height)
        st.metric("BMI", bmi)
    st.button("Save Personal Info")

# Medical History Section
with st.expander("Medical History"):
    st.write("Manage your medical conditions below.")
    conditions = [
        {"name": "Diabetes", "date": "2015-03-10", "color": "#e76f51"},
        {"name": "Hypertension", "date": "2018-07-22", "color": "#2a9d8f"}
    ]
    for cond in conditions:
        st.markdown(f"<span style='background: {cond['color']}; color: #fff; border-radius: 6px; padding: 0.3rem 0.7rem; margin-right: 0.5rem;'>{cond['name']}</span> <span style='color: #888;'>Diagnosed: {cond['date']}</span>", unsafe_allow_html=True)
        if st.button(f"Details: {cond['name']}"):
            st.info(f"Details for {cond['name']} (popup placeholder)")
    if st.button("Add New Condition"):
        st.session_state.show_add_condition = True
    if st.session_state.get('show_add_condition', False):
        st.markdown("**Add New Condition**")
        new_cond = st.text_input("Condition Name")
        new_date = st.date_input("Date Diagnosed")
        if st.button("Save Condition"):
            st.success("(Demo) Condition added!")
            st.session_state.show_add_condition = False
        if st.button("Cancel"):
            st.session_state.show_add_condition = False

# Family History Section
with st.expander("Family History"):
    st.write("Add family members and hereditary conditions.")
    family_members = [
        {"name": "Mother", "relation": "Mother", "conditions": ["Diabetes"]},
        {"name": "Father", "relation": "Father", "conditions": ["Hypertension"]}
    ]
    for member in family_members:
        st.markdown(f"<b>{member['name']}</b> <span style='color: #888;'>({member['relation']})</span>", unsafe_allow_html=True)
        st.write(f"Hereditary Conditions: {', '.join(member['conditions'])}")
    if st.button("Add Family Member"):
        st.session_state.show_add_family = True
    if st.session_state.get('show_add_family', False):
        st.markdown("**Add Family Member**")
        fam_name = st.text_input("Family Member Name")
        fam_relation = st.selectbox("Relationship", ["Mother", "Father", "Sibling", "Child", "Other"])
        fam_conditions = st.text_input("Hereditary Conditions (comma separated)")
        if st.button("Save Family Member"):
            st.success("(Demo) Family member added!")
            st.session_state.show_add_family = False
        if st.button("Cancel"):
            st.session_state.show_add_family = False

# Current Medications Section
with st.expander("Current Medications"):
    st.write("Manage your current medications.")
    medications = [
        {"name": "Metformin", "dosage": "500mg", "frequency": "Twice daily", "start": "2015-03-15", "end": ""},
        {"name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily", "start": "2018-07-25", "end": ""}
    ]
    for med in medications:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{med['name']}** - {med['dosage']} ({med['frequency']})")
            st.write(f"Started: {med['start']}")
        with col2:
            if st.button(f"Edit {med['name']}"):
                st.info(f"Edit {med['name']} (modal placeholder)")
        with col3:
            if st.button(f"Delete {med['name']}"):
                st.warning(f"Delete {med['name']} (confirmation placeholder)")
    if st.button("Add Medication"):
        st.session_state.show_add_medication = True
    if st.session_state.get('show_add_medication', False):
        st.markdown("**Add New Medication**")
        med_name = st.text_input("Medication Name")
        med_dosage = st.text_input("Dosage")
        med_frequency = st.selectbox("Frequency", ["Once daily", "Twice daily", "Three times daily", "As needed"])
        med_start = st.date_input("Start Date")
        med_reminder = st.checkbox("Set reminder")
        if st.button("Save Medication"):
            st.success("(Demo) Medication added!")
            st.session_state.show_add_medication = False
        if st.button("Cancel"):
            st.session_state.show_add_medication = False

# Allergies and Restrictions Section
with st.expander("Allergies and Dietary Restrictions"):
    st.write("Manage your allergies and dietary restrictions.")
    allergies = [
        {"type": "Medication", "name": "Penicillin", "severity": "High", "reaction": "Rash, difficulty breathing"},
        {"type": "Food", "name": "Peanuts", "severity": "High", "reaction": "Anaphylaxis"}
    ]
    for allergy in allergies:
        severity_color = "#e76f51" if allergy["severity"] == "High" else "#e9c46a"
        st.markdown(f"<span style='background: {severity_color}; color: #fff; border-radius: 6px; padding: 0.3rem 0.7rem; margin-right: 0.5rem;'>{allergy['type']}</span> <b>{allergy['name']}</b> <span style='color: #888;'>({allergy['severity']})</span>", unsafe_allow_html=True)
        st.write(f"Reaction: {allergy['reaction']}")
    if st.button("Add Allergy"):
        st.session_state.show_add_allergy = True
    if st.session_state.get('show_add_allergy', False):
        st.markdown("**Add New Allergy**")
        allergy_type = st.selectbox("Allergy Type", ["Medication", "Food", "Environmental", "Other"])
        allergy_name = st.text_input("Allergy Name")
        allergy_severity = st.selectbox("Severity", ["Low", "Medium", "High"])
        allergy_reaction = st.text_area("Reaction Description")
        if st.button("Save Allergy"):
            st.success("(Demo) Allergy added!")
            st.session_state.show_add_allergy = False
        if st.button("Cancel"):
            st.session_state.show_add_allergy = False
    
    st.markdown("---")
    st.markdown("**Dietary Restrictions**")
    restrictions = ["Gluten-free", "Dairy-free", "Vegetarian"]
    for restriction in restrictions:
        st.write(f"• {restriction}")
    if st.button("Add Dietary Restriction"):
        st.session_state.show_add_restriction = True
    if st.session_state.get('show_add_restriction', False):
        st.markdown("**Add Dietary Restriction**")
        restriction_type = st.selectbox("Restriction Type", ["Gluten-free", "Dairy-free", "Vegetarian", "Vegan", "Custom"])
        if restriction_type == "Custom":
            custom_restriction = st.text_input("Custom Restriction")
        restriction_notes = st.text_area("Notes")
        if st.button("Save Restriction"):
            st.success("(Demo) Restriction added!")
            st.session_state.show_add_restriction = False
        if st.button("Cancel"):
            st.session_state.show_add_restriction = False 