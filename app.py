import streamlit as st
from openai import OpenAI
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="Plumbing Forensics AI 2.0", page_icon="🪠", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if "step" not in st.session_state:
    st.session_state.step = 1
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "learned_rules" not in st.session_state:
    st.session_state.learned_rules = []  # Stores user corrections

# --- CSS STYLING ---
st.markdown("""
<style>
    .big-header { font-size: 2.5rem; font-weight: 800; color: #1e3a8a; }
    .question-text { font-size: 1.5rem; font-weight: 600; color: #374151; margin-bottom: 20px; }
    .ai-card { background-color: #f0fdf4; border: 1px solid #22c55e; padding: 25px; border-radius: 10px; margin-top: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .rule-box { background-color: #fffbeb; border-left: 5px solid #f59e0b; padding: 10px; font-size: 0.9rem; color: #92400e; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def encode_image(uploaded_file):
    """Encodes image to Base64 for OpenAI"""
    if uploaded_file is None:
        return None
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def get_ai_diagnosis(api_key, image_file, answers, rules):
    """Sends all data + image + rules to GPT-4o"""
    if not api_key:
        return "⚠️ Error: Please enter an OpenAI API Key in the sidebar."

    client = OpenAI(api_key=api_key)
    
    # 1. Construct the Context from Questionnaire
    context_text = f"""
    **Case Data:**
    - Property Year: {answers.get('year', 'Unknown')}
    - Damage Location: {answers.get('location', 'Unknown')}
    - Context (What is above): {answers.get('above', 'Unknown')}
    - Symptoms: {answers.get('symptoms', 'None')}
    - Water Temp/Character: {answers.get('character', 'Unknown')}
    """

    # 2. Add Learned Rules (The "Memory")
    if rules:
        context_text += "\n\n**USER CORRECTIONS (LEARNED RULES):**\n"
        for rule in rules:
            context_text += f"- {rule}\n"

    # 3. The Senior Plumber Prompt
    system_prompt = """
    You are a U.S. Licensed Senior Plumber and Forensic Specialist.
    Perform a Root Cause Analysis based on the provided text data and the attached image (if any).
    
    thinking_process:
    1. Check property age for banned materials (Polybutylene, Galvanized).
    2. Apply 'Path of Least Resistance' logic based on the location.
    3. IF specific "Learned Rules" are provided, prioritize them over standard logic.
    
    Output Format:
    ## 🛠️ The Forensic Profile
    - **Visual Analysis:** (What do you see in the photo?)
    - **Suspected Pipe Material:** (Based on age/visuals)
    - **Logic Path:** (Chain of Thought)

    ## 🔍 Root Cause Probabilities
    | Probability | Suspect | Reason |
    | :--- | :--- | :--- |
    | **High** | [Suspect 1] | [Why?] |
    | **Medium** | [Suspect 2] | [Why?] |

    ## 📋 Recommended Action Plan
    1. [Immediate Test]
    2. [Secondary Test]
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": [{"type": "text", "text": context_text}]}
    ]

    # 4. Attach Image if present
    if image_file:
        b64_img = encode_image(image_file)
        messages[0]["content"] += "\n(An image of the damage has been provided.)"
        messages[1]["content"].append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
        })

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"API Error: {str(e)}"

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ System Config")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    st.divider()
    st.subheader("🧠 Learned Logic")
    if st.session_state.learned_rules:
        for rule in st.session_state.learned_rules:
            st.markdown(f"✅ *{rule}*")
    else:
        st.info("No corrections learned yet.")
    
    if st.button("Restart Session"):
        st.session_state.step = 1
        st.session_state.answers = {}
        st.rerun()

# --- MAIN APP FLOW ---
st.markdown('<div class="big-header">🪠 Plumbing Forensics AI 2.0</div>', unsafe_allow_html=True)
st.progress(st.session_state.step * 25)

# === STEP 1: INTAKE & PHOTO ===
if st.session_state.step == 1:
    st.markdown('<div class="question-text">Step 1: The Evidence</div>', unsafe_allow_html=True)
    
    # Basic Data
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.answers['year'] = st.number_input("Year Built", 1900, 2025, 1995)
    with c2:
        img = st.file_uploader("Upload Photo of Leak (Optional)", type=['png', 'jpg', 'jpeg'])
        if img:
            st.session_state.answers['image'] = img
            st.image(img, width=200)

    if st.button("Start Triage ➡️", type="primary"):
        st.session_state.step = 2
        st.rerun()

# === STEP 2: DYNAMIC TRIAGE (Branching Questions) ===
elif st.session_state.step == 2:
    st.markdown('<div class="question-text">Step 2: Where is the water coming from?</div>', unsafe_allow_html=True)
    
    # Question 1: Location
    loc = st.radio("Select the primary location:", ["Ceiling", "Floor / Carpet", "Wall / Cabinet"], index=None)
    
    if loc:
        st.session_state.answers['location'] = loc
        st.divider()
        
        # BRANCH A: CEILING
        if loc == "Ceiling":
            st.info("Checking Gravity Sources...")
            above = st.radio("What is directly above this spot?", ["Roof / Attic", "Bathroom / Kitchen", "Nothing / Another Room"])
            if above:
                st.session_state.answers['above'] = above
                st.session_state.answers['character'] = st.selectbox("When does it leak?", ["Only when it rains", "Constant drip", "Only when showering upstairs"])
                if st.button("Analyze Logic ➡️"):
                    st.session_state.step = 3
                    st.rerun()

        # BRANCH B: FLOOR
        elif loc == "Floor / Carpet":
            st.info("Checking Hydrostatic & Supply Sources...")
            temp = st.radio("Touch the water. Is it:", ["Warm / Hot", "Cold / Room Temp"])
            if temp:
                st.session_state.answers['character'] = temp
                st.session_state.answers['above'] = "N/A (Floor Leak)"
                st.session_state.answers['symptoms'] = st.text_input("Any specific smell or sound?", "e.g., Hissing sound, Musty smell")
                if st.button("Analyze Logic ➡️"):
                    st.session_state.step = 3
                    st.rerun()

        # BRANCH C: WALL
        elif loc == "Wall / Cabinet":
            st.info("Checking Risers & Drains...")
            st.session_state.answers['above'] = "Inside Wall"
            st.session_state.answers['character'] = st.text_input("Is the wall soft or bubbling?", "Yes/No")
            st.session_state.answers['symptoms'] = st.text_input("Is this wall shared with a bathroom?", "Yes, shower is behind it")
            if st.button("Analyze Logic ➡️"):
                st.session_state.step = 3
                st.rerun()

# === STEP 3: THE AI DIAGNOSIS ===
elif st.session_state.step == 3:
    st.markdown("### 🔍 Senior Plumber Analysis")
    
    # Run the AI
    if "diagnosis" not in st.session_state:
        with st.spinner("Analyzing visual evidence and structural logic..."):
            img_file = st.session_state.answers.get('image')
            result = get_ai_diagnosis(api_key, img_file, st.session_state.answers, st.session_state.learned_rules)
            st.session_state.diagnosis = result
    
    st.markdown(f'<div class="ai-card">{st.session_state.diagnosis}</div>', unsafe_allow_html=True)
    
    st.divider()
    st.subheader("🎓 Feedback Loop")
    st.write("Was this diagnosis correct?")
    
    c1, c2 = st.columns(2)
    if c1.button("✅ Yes, Correct"):
        st.success("Logic reinforced.")
        if st.button("Start New Case"):
            del st.session_state['diagnosis']
            st.session_state.step = 1
            st.rerun()
            
    if c2.button("❌ No, incorrect"):
        st.session_state.step = 4
        st.rerun()

# === STEP 4: THE LEARNING PHASE ===
elif st.session_state.step == 4:
    st.error("Diagnostic Mismatch Detected.")
    st.markdown("Please explain the **actual** cause so I can refine my logic for the next case.")
    
    correction = st.text_input("What was the real issue?", placeholder="e.g. It wasn't the slab, it was a shower valve leaking down the wall.")
    
    if st.button("Update Neural Logic"):
        # Add to session rules
        new_rule = f"User Correction: When symptoms match '{st.session_state.answers.get('character')}', consider '{correction}' as high priority."
        st.session_state.learned_rules.append(new_rule)
        
        st.success("Logic Updated! I will apply this rule to future queries in this session.")
        del st.session_state['diagnosis']
        st.session_state.step = 1
        st.rerun()