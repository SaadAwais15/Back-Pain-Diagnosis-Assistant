import streamlit as st
from dataclasses import dataclass
from typing import Set, Dict
from queue import PriorityQueue

@dataclass
class Diagnosis:
    name: str
    required_symptoms: Set[str]
    optional_symptoms: Set[str]
    red_flags: Set[str]
    suggested_tests: Set[str]
    suggested_treatments: Set[str]

# ------------------ Knowledge Base ------------------
kb: Dict[str, Diagnosis] = {
    "muscular_strain": Diagnosis(
        name="Muscular Strain",
        required_symptoms={"localized_back_pain"},
        optional_symptoms={"pain_with_movement", "muscle_tightness", "improves_with_rest", "stiffness_morning"},
        red_flags=set(),
        suggested_tests={"Physical Examination"},
        suggested_treatments={"Rest", "Physiotherapy", "NSAIDs"}
    ),
    "disc_herniation": Diagnosis(
        name="Disc Herniation",
        required_symptoms={"radiating_leg_pain", "pain_shoots_when_cough_or_sneeze", "sharp_burning_back_or_leg_pain"},
        optional_symptoms={"numbness", "tingling", "leg_weakness", "pain_in_buttocks_or_thigh", "pain_in_foot", "pain_when_lifting_or_twisting", "pain_in_arm_or_shoulder"},
        red_flags={"bladder_dysfunction", "saddle_anesthesia", "progressive_leg_weakness"},
        suggested_tests={"MRI", "CT Scan", "Physical Examination"},
        suggested_treatments={"Physical Therapy", "Pain Management", "Surgery if severe"}
    ),
    "sciatica": Diagnosis(
        name="Sciatica / Radiculopathy",
        required_symptoms={"radiating_leg_pain", "pain_shoots_when_cough_or_sneeze", "numbness", "tingling"},
        optional_symptoms={"leg_weakness", "urinary_incontinence", "fecal_incontinence", "pain_on_lifting_leg", "leg_pain_below_knee"},
        red_flags={"urinary_incontinence", "fecal_incontinence"},
        suggested_tests={"MRI", "X-Ray", "Nerve Conduction Study"},
        suggested_treatments={"NSAIDs", "Physical Therapy", "Epidural Steroid Injection", "Surgery if severe"}
    )
}

# ------------------ Session State Init ------------------
if "provided" not in st.session_state:
    st.session_state.provided = set()
if "asked" not in st.session_state:
    st.session_state.asked = set()
if "finished" not in st.session_state:
    st.session_state.finished = False
if "symptom_list" not in st.session_state:
    st.session_state.symptom_list = []
if "possible_diags" not in st.session_state:
    st.session_state.possible_diags = set(kb.keys())

def build_symptom_list(kb):
    symptoms = set()
    for diag in kb.values():
        symptoms.update(diag.required_symptoms)
        symptoms.update(diag.optional_symptoms)
    return list(symptoms)

# ------------------ Streamlit UI ------------------
# Custom CSS for medical-inspired styling
st.markdown("""
<style>
    .main {
        background-color: #f0f8ff;  /* Light blue background */
    }
    .stButton>button {
        background-color: #4CAF50;  /* Green for yes */
        color: white;
        border-radius: 10px;
        font-size: 16px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .no-button {
        background-color: #f44336 !important;  /* Red for no */
    }
    .no-button:hover {
        background-color: #da190b !important;
    }
    .title {
        color: #2E86C1;  /* Medical blue */
        font-family: 'Arial', sans-serif;
        text-align: center;
    }
    .question-box {
        background-color: #ffffff;
        border: 2px solid #2E86C1;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .question-text {
        color: black;
        font-weight: bold;
    }
    .diagnosis-card {
        background-color: #ffffff;
        border: 2px solid #28B463;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .red-flag {
        background-color: #ffe6e6;
        border: 2px solid #E74C3C;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='title'>🩺 Back Pain Diagnosis Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #2E86C1;'>Using Best-First Search to guide your diagnosis process 💡</p>", unsafe_allow_html=True)

if not st.session_state.finished:
    if not st.session_state.symptom_list:
        st.session_state.symptom_list = build_symptom_list(kb)

    # Update possible diagnoses based on current provided and asked symptoms
    for diag in list(st.session_state.possible_diags):
        if any(req in st.session_state.asked and req not in st.session_state.provided for req in kb[diag].required_symptoms):
            st.session_state.possible_diags.remove(diag)

    # Collect candidate symptoms from possible diagnoses
    candidate_symptoms = set()
    for diag in st.session_state.possible_diags:
        candidate_symptoms.update(kb[diag].required_symptoms | kb[diag].optional_symptoms)

    # Get list of unasked candidate symptoms
    candidates = [s for s in st.session_state.symptom_list if s not in st.session_state.asked and s in candidate_symptoms]

    if candidates:
        # Compute heuristic for each candidate: negative count of possible diagnoses that have this symptom (lower heuristic = higher priority)
        heuristic = {}
        for symptom in candidates:
            count = sum(1 for d in st.session_state.possible_diags if symptom in kb[d].required_symptoms or symptom in kb[d].optional_symptoms)
            heuristic[symptom] = -count  # More negative for symptoms in more diagnoses

        # Use PriorityQueue to select the next symptom (smallest heuristic first)
        queue = PriorityQueue()
        for symptom in candidates:
            queue.put((heuristic[symptom], symptom))

        if not queue.empty():
            h, symptom = queue.get()
            st.markdown(f"<div class='question-box'><span class='question-text'>🤔 Does the patient have <strong>'{symptom.replace('_',' ')}'</strong>?</span></div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2, gap="small")
            with col1:
                yes = st.button("✅ Yes", key=f"yes_{symptom}")
            with col2:
                no = st.button("❌ No", key=f"no_{symptom}", help="Click if the patient does not have this symptom")

            if yes:
                st.session_state.provided.add(symptom)
                st.session_state.asked.add(symptom)
                st.rerun()
            elif no:
                st.session_state.asked.add(symptom)
                st.rerun()
    else:
        st.session_state.finished = True

if st.session_state.finished:
    st.markdown("<div class='diagnosis-card'>", unsafe_allow_html=True)
    st.markdown("### 🎉 Diagnosis Complete!")
    st.write("**🩹 Symptoms provided by patient:**", ", ".join(sorted(st.session_state.provided)) if st.session_state.provided else "None")

    # Score final diagnosis (only among possible diagnoses, but since finished, use all or the top)
    scores = {}
    for key in st.session_state.possible_diags or kb.keys():  # If no possible, fallback to all
        diag = kb[key]
        score = 2 * len(diag.required_symptoms.intersection(st.session_state.provided))
        score += len(diag.optional_symptoms.intersection(st.session_state.provided))
        scores[key] = score
    if scores:
        final_diag_key = max(scores, key=lambda k: scores[k])
        final_diag = kb[final_diag_key]
        st.write(f"**🏥 Final Diagnosis:** {final_diag.name}")
    else:
        st.write("**🏥 Final Diagnosis:** Unable to determine (no matching diagnoses)")

    if scores:
        red_flags_detected = st.session_state.provided.intersection(final_diag.red_flags)
        if red_flags_detected:
            st.markdown("<div class='red-flag'>", unsafe_allow_html=True)
            st.write("***🚨 URGENT MEDICAL ATTENTION ADVISED ***")
            st.write("Red Flag Symptoms Detected:", ", ".join(red_flags_detected))
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.success("✅ No immediate red flags detected.")

        st.write("**🧪 Suggested Tests:**", ", ".join(final_diag.suggested_tests))
        st.write("**💊 Suggested Treatments:**", ", ".join(final_diag.suggested_treatments))
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🔄 Start New Diagnosis"):
        st.session_state.provided.clear()
        st.session_state.asked.clear()
        st.session_state.finished = False
        st.session_state.symptom_list.clear()
        st.session_state.possible_diags = set(kb.keys())
