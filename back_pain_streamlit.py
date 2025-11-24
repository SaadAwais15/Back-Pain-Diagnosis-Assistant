import streamlit as st
from dataclasses import dataclass
from typing import Set, Dict

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
        required_symptoms={"local back pain"},
        optional_symptoms={
            "pain when moving",
            "muscle tightness",
            "pain gets better with rest",
            "morning stiffness"
        },
        red_flags=set(),
        suggested_tests={"Physical Examination"},
        suggested_treatments={"Rest", "Physiotherapy", "NSAIDs"}
    ),

    "disc_herniation": Diagnosis(
        name="Disc Herniation",
        required_symptoms={
            "radiating pain from back to leg",
            "pain worse with cough or sneeze",
            "sharp back or leg pain"
        },
        optional_symptoms={
            "numbness",
            "tingling",
            "leg weakness",
            "buttock or thigh pain",
            "foot pain",
            "pain when bending or twisting",
            "arm or shoulder pain"
        },
        red_flags={
            "trouble controlling bladder",
            "numbness between legs",
            "leg weakness"
        },
        suggested_tests={"MRI", "CT Scan", "Physical Examination"},
        suggested_treatments={"Physical Therapy", "Pain Management", "Surgery if severe"}
    ),

    "sciatica": Diagnosis(
        name="Sciatica / Nerve Compression",
        required_symptoms={
            "radiating pain from back to leg",
            "pain worse with cough or sneeze",
            "numbness",
            "tingling"
        },
        optional_symptoms={
            "leg weakness",
            "loss of bladder control",
            "loss of bowel control",
            "pain when raising leg",
            "pain below knee"
        },
        red_flags={
            "loss of bladder control",
            "loss of bowel control"
        },
        suggested_tests={"MRI", "X-Ray", "Nerve Conduction Study"},
        suggested_treatments={
            "NSAIDs",
            "Physical Therapy",
            "Epidural Steroid Injection",
            "Surgery if severe"
        }
    )
}

# ------------------ Session State Init ------------------
if "provided" not in st.session_state:
    st.session_state.provided = set()
if "diagnosed" not in st.session_state:
    st.session_state.diagnosed = False

def build_symptom_list(kb):
    symptoms = set()
    for diag in kb.values():
        symptoms.update(diag.required_symptoms)
        symptoms.update(diag.optional_symptoms)
    return sorted(list(symptoms))

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
    .title {
        color: #2E86C1;  /* Medical blue */
        font-family: 'Arial', sans-serif;
        text-align: center;
    }
    .input-box {
        background-color: transparent;
        border: 2px solid #2E86C1;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .diagnosis-card {
        background-color: transparent;
        border: 2px solid #28B463;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .red-flag {
        background-color: transparent;
        border: 2px solid #E74C3C;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .large-text {
        font-size: 36px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='title'>🩺 Back Pain Diagnosis Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #2E86C1;'>Enter patient symptoms and get a diagnosis using Best-First Search 💡</p>", unsafe_allow_html=True)

symptom_list = build_symptom_list(kb)

if not st.session_state.diagnosed:
    st.write("**📝 Enter Patient Symptoms:**")
    st.write("Please select at least 4 symptoms from the list below. Suggestions will appear as you type.")
    
    selected_symptoms = st.multiselect(
        "Select symptoms (type to search and select):",
        options=symptom_list,
        default=[],
        help="Choose from the available symptoms. At least 4 are required for diagnosis."
    )
    
    if len(selected_symptoms) < 4:
        st.warning("⚠️ Please select at least 4 symptoms to proceed with diagnosis.")
        diagnose_button = st.button("Diagnose", disabled=True)
    else:
        diagnose_button = st.button("🔍 Diagnose")
    
    if diagnose_button:
        st.session_state.provided = set(selected_symptoms)
        st.session_state.diagnosed = True
        st.rerun()

if st.session_state.diagnosed:
    st.markdown("<div class='diagnosis-card'>", unsafe_allow_html=True)
    st.write("### <span style='color: red;'>➕</span> Diagnosis Complete!", unsafe_allow_html=True)
    st.write("**🩹 Symptoms provided by patient:**", ", ".join(sorted(st.session_state.provided)) if st.session_state.provided else "None")
    st.markdown("</div>", unsafe_allow_html=True)

    # Score final diagnosis using best-first like scoring (prioritize based on matches)
    scores = {}
    for key, diag in kb.items():
        score = 2 * len(diag.required_symptoms.intersection(st.session_state.provided))
        score += len(diag.optional_symptoms.intersection(st.session_state.provided))
        scores[key] = score
    
    if scores:
        # Best-first: select the one with highest score (most matches)
        final_diag_key = max(scores, key=lambda k: scores[k])
        final_diag = kb[final_diag_key]
        
        st.markdown("<div class='red-flag'>", unsafe_allow_html=True)
        st.markdown(f"<p class='large-text'>🏥 Final Diagnosis: {final_diag.name}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        red_flags_detected = st.session_state.provided.intersection(final_diag.red_flags)
        if red_flags_detected:
            st.write("***🚨 URGENT MEDICAL ATTENTION ADVISED ***")
            st.write("Red Flag Symptoms Detected:", ", ".join(red_flags_detected))
        else:
            st.success("✅ No immediate red flags detected.")

        st.write("**🧪 Suggested Tests:**", ", ".join(final_diag.suggested_tests))
        st.write("**💊 Suggested Treatments:**", ", ".join(final_diag.suggested_treatments))
    else:
        st.write("**🏥 Final Diagnosis:** Unable to determine (no matching diagnoses)")

    if st.button("🔄 Start New Diagnosis"):
        st.session_state.provided.clear()
        st.session_state.diagnosed = False
