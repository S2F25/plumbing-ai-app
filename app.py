import streamlit as st
from openai import OpenAI
import base64
import time
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="Snap2Fix: AI Plumber", page_icon="🪠", layout="wide")

# --- SESSION STATE ---
if "step" not in st.session_state: st.session_state.step = 1
if "data" not in st.session_state: st.session_state.data = {}
if "ai_questions" not in st.session_state: st.session_state.ai_questions = []

# --- MOCK DATABASE (Simulating Zillow/Google Maps API) ---
# In production, replace this with requests.get('https://api.bridgedataoutput.com/...')
MOCK_PROPERTY_DB = {
    "123 Main St": {"year": 1954, "sqft": 1200, "plans": ["Ranch Style (Crawlspace)", "Bungalow (Slab)"]},
    "456 Oak Ave": {"year": 1988, "sqft": 2400, "plans": ["2-Story Colonial", "Split Level"]},
    "789 Pine Rd": {"year": 2015, "sqft": 3000, "plans": ["Modern Open Concept", "Traditional Basement"]}
}

# --- HELPER FUNCTIONS ---
def encode_image(uploaded_file):
    if uploaded_file is None: return None
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def generate_dynamic_questions(api_key, case_data, image_file):
    """
    STEP 1 AI CALL:
    Looks at the photo and house info, then generates 3 investigative questions.
    Returns: JSON list of questions.
    """
    client = OpenAI(api_key=api_key)
    
    # Context for the AI
    prompt = f"""
    You are a Senior Plumber investigating a leak.
    House Built: {case_data.get('year')}
    Floor Plan: {case_data.get('plan')}
    Description: {case_data.get('desc')}
    
    Task: Analyze the image (if provided) and the house stats. 
    Generate 3 specific, simple questions to ask the homeowner to narrow down the root cause.
    Return ONLY a raw JSON list of strings. Example: ["Does it hurt when you press?", "Is the water hot?", "Smell?"]
    """
    
    messages = [
        {"role": "system", "content": "You are a forensic plumbing AI. Output JSON only."},
        {"role": "user", "content": [{"type": "text", "text": prompt}]}
    ]

    if image_file:
        b64_img = encode_image(image_file)
        messages[1]["content"].append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
        })

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"}
        )
        # Parse JSON
        result = json.loads(response.choices[0].message.content)
        return result.get("questions", ["Is the water constant or intermittent?", "Is it warm?", "Any recent repairs?"])
    except Exception as e:
        st.error(f"AI Error: {e}")
        return ["Is the leak constant?", "Is the water warm?", "Is there a bathroom above?"]

def get_final_diagnosis(api_key, case_data, questions, answers, image_file):
    """
    STEP 2 AI CALL:
    Takes the answers and gives the final verdict.
    """
    client = OpenAI(api_key=api_key)
    
    # Build the interview transcript
    interview_text = ""
    for q, a in zip(questions, answers):
        interview_text += f"Q: {q}\nA: {a}\n"

    prompt = f"""
    Analyze this Plumbing Case:
    - Property: {case_data.get('year')} Built, {case_data.get('plan')}
    - Initial Issue: {case_data.get('desc')}
    - Interview Results:
    {interview_text}
    
    Provide a Root Cause Analysis.
    1. Most Likely Cause.
    2. Recommended Action.
    3. Estimated Complexity (1-10).
    """

    messages = [{"role": "system", "content": "You are a Senior Plumber."}, 
                {"role": "user", "content": prompt}]
    
    if image_file:
        b64_img = encode_image(image_file)
        messages[1]["content"] = [{"type": "text", "text": prompt}, 
                                  {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}]

    response = client.chat.completions.create(model="gpt-4o", messages=messages)
    return response.choices[0].message.content

# --- SIDEBAR (Secure Key) ---
with st.sidebar:
    st.title("⚙️ Snap2Fix Config")
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        st.success("✅ License Active")
    else:
        api_key = st.text_input("Enter API Key", type="password")

# --- MAIN APP ---
st.markdown("""
    <style>
    .step-header { color: #1e3a8a; font-size: 1.5rem; font-weight: bold; margin-bottom: 10px; }
    .stButton button { width: 100%; border-radius: 5px; height: 50px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🪠 Snap2Fix: Intelligent Diagnostics")

# === STEP 1: PROPERTY INTELLIGENCE ===
if st.session_state.step == 1:
    st.markdown('<div class="step-header">1. Property Profile</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        address = st.text_input("Enter Property Address", placeholder="e.g. 123 Main St")
    with col2:
        st.write("") # Spacer
        fetch_btn = st.button("🔍 Auto-Fetch")

    if fetch_btn and address:
        # SIMULATION: Fetching data from Zillow/Google
        with st.spinner("Connecting to Property Records Database..."):
            time.sleep(1.5) # Fake API delay
            
            # Simple fuzzy matching for demo
            found_data = None
            for key in MOCK_PROPERTY_DB:
                if key.lower() in address.lower():
                    found_data = MOCK_PROPERTY_DB[key]
                    break
            
            if found_data:
                st.session_state.data['year'] = found_data['year']
                st.session_state.data['plans'] = found_data['plans']
                st.success(f"Found Record: Built {found_data['year']}")
            else:
                st.warning("Address not found in mock DB. Using manual entry.")
                st.session_state.data['year'] = 1990
                st.session_state.data['plans'] = ["Standard Layout"]

    # If data is fetched or manually entered
    if 'year' in st.session_state.data:
        st.session_state.data['year'] = st.number_input("Year Built", value=st.session_state.data['year'])
        st.session_state.data['plan'] = st.selectbox("Select Floor Plan", st.session_state.data.get('plans', ["Unknown"]))
        
        if st.button("Confirm Property Info ➡️"):
            st.session_state.step = 2
            st.rerun()

# === STEP 2: MULTI-MODAL INTAKE ===
elif st.session_state.step == 2:
    st.markdown('<div class="step-header">2. The Evidence</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload Photo or Video", type=['png', 'jpg', 'jpeg', 'mp4', 'mov'])
    
    if uploaded_file:
        file_type = uploaded_file.type.split('/')[0]
        if file_type == "video":
            st.video(uploaded_file)
            st.info("ℹ️ Video uploaded. AI will analyze the visual context.")
        else:
            st.image(uploaded_file, width=300)
            
        st.session_state.data['media'] = uploaded_file
        st.session_state.data['type'] = file_type

    # Optional Description
    desc = st.text_area("Describe the issue (Optional)", placeholder="e.g. Wet spot on ceiling, smells musty...")
    st.session_state.data['desc'] = desc if desc else "No text description provided."

    if st.button("Analyze & Generate Questions ➡️", type="primary"):
        if not api_key:
            st.error("Please enter API Key in sidebar.")
        else:
            with st.spinner("AI is analyzing the visuals and generating interview questions..."):
                # Call AI Step 1
                img = st.session_state.data.get('media') if st.session_state.data.get('type') == 'image' else None
                questions = generate_dynamic_questions(api_key, st.session_state.data, img)
                st.session_state.ai_questions = questions
                st.session_state.step = 3
                st.rerun()

# === STEP 3: AI INTERROGATION ===
elif st.session_state.step == 3:
    st.markdown('<div class="step-header">3. Detective Mode</div>', unsafe_allow_html=True)
    st.write("The AI needs a few specific details to narrow down the cause.")
    
    with st.form("interview_form"):
        answers = []
        for i, q in enumerate(st.session_state.ai_questions):
            st.write(f"**Q{i+1}: {q}**")
            # We use a unique key for each text input
            ans = st.text_input(f"Your Answer for Q{i+1}", key=f"q_{i}")
            answers.append(ans)
            st.write("---")
            
        if st.form_submit_button("Get Final Diagnosis 🚀"):
            st.session_state.data['answers'] = answers
            st.session_state.step = 4
            st.rerun()

# === STEP 4: DIAGNOSIS & ACTION ===
elif st.session_state.step == 4:
    st.markdown('<div class="step-header">4. Forensic Report</div>', unsafe_allow_html=True)
    
    if "final_report" not in st.session_state:
        with st.spinner("Crunching data... connecting clues..."):
            img = st.session_state.data.get('media') if st.session_state.data.get('type') == 'image' else None
            report = get_final_diagnosis(
                api_key, 
                st.session_state.data, 
                st.session_state.ai_questions, 
                st.session_state.data['answers'], 
                img
            )
            st.session_state.final_report = report

    st.success("Analysis Complete")
    st.markdown(f"""
    <div style="background-color:#f8fafc; padding:20px; border-radius:10px; border:1px solid #e2e8f0;">
        {st.session_state.final_report}
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("💰 Get Repair Estimate")
    with col2:
        if st.button("🔄 New Case"):
            st.session_state.clear()
            st.rerun()