import streamlit as st
from openai import OpenAI
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="Plumbing Forensics AI Pro", page_icon="🪠", layout="wide")

# --- CSS STYLING ---
st.markdown("""
<style>
    .header { font-size: 2.2rem; font-weight: 800; color: #1e3a8a; }
    .ai-box { background-color: #f0fdf4; border: 1px solid #22c55e; padding: 25px; border-radius: 10px; margin-top: 20px; font-family: sans-serif;}
    .report-title { color: #166534; font-weight: bold; font-size: 1.2rem; margin-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

# --- SYSTEM PROMPT (THE PERSONA) ---
SYSTEM_PROMPT = """
You are a U.S. Licensed Senior Plumber and Forensic Specialist.
You are analyzing a potential water damage issue based on user text and visual evidence.

YOUR TASKS:
1. Visual Analysis: identifying water stain patterns (concentric rings = intermittent), mold colors, or pipe materials (Copper, PEX, Polybutylene, Galvanized).
2. Root Cause Identification: Combine visual cues with the home's age and description.
3. Safety Check: Flag potential code violations or health hazards (e.g., Black Mold, Lead, Sewer Gas).

OUTPUT FORMAT:
## 🔍 Visual Observations
[What do you see in the photo?]

## 🛠️ The Forensic Profile
- **Suspected Source:** [e.g., Shower Pan, Slab Leak, Roof Boot]
- **Confidence Score:** [High/Medium/Low]

## 📋 Action Plan
1. [Step 1]
2. [Step 2]
"""

# --- HELPER: IMAGE ENCODER ---
def encode_image(uploaded_file):
    """Converts the uploaded file to Base64 for the API"""
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# --- MAIN LOGIC ---
def analyze_case(api_key, age, foundation, loc, desc, image_file):
    if not api_key:
        return "⚠️ Please enter your OpenAI API Key in the sidebar."
    
    client = OpenAI(api_key=api_key)
    
    # Prepare the content list (Text + Optional Image)
    content_payload = [
        {"type": "text", "text": f"Property Built: {age}. Foundation: {foundation}. Location: {loc}. Description: {desc}. Analyze this plumbing issue."}
    ]
    
    # If user uploaded an image, add it to the payload
    if image_file is not None:
        base64_image = encode_image(image_file)
        content_payload.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
        })

    try:
        response = client.chat.completions.create(
            model="gpt-4o", # "gpt-4o" has Vision capabilities
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content_payload}
            ],
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# --- UI LAYOUT ---
with st.sidebar:
    st.title("⚙️ Settings")
    api_key = st.text_input("OpenAI API Key", type="password", help="Get this from platform.openai.com")
    st.info("Note: This app requires GPT-4o which costs a few cents per run.")

st.markdown('<div class="header">🪠 Plumbing Forensics AI: Vision Edition</div>', unsafe_allow_html=True)
st.write("Upload a photo of the damage, and the AI will inspect it like a pro.")
st.divider()

# TWO-COLUMN LAYOUT
left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("1. Case Details")
    prop_age = st.number_input("Year Built", 1900, 2025, 1990)
    foundation = st.selectbox("Foundation", ["Slab on Grade", "Crawlspace", "Basement"])
    location = st.selectbox("Location", ["Ceiling", "Wall", "Floor", "Under Sink", "Exterior"])
    desc = st.text_area("Description", "e.g. Water is dripping slowly and smells musty.")
    
    st.subheader("2. Visual Evidence")
    uploaded_image = st.file_uploader("Upload Photo (Optional)", type=["jpg", "png", "jpeg"])
    if uploaded_image:
        st.image(uploaded_image, caption="Evidence Uploaded", width=300)

with right_col:
    st.subheader("3. Forensic Report")
    analyze_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)
    
    if analyze_btn:
        with st.spinner("Analyzing structural data and visual evidence..."):
            result = analyze_case(api_key, prop_age, foundation, location, desc, uploaded_image)
            st.markdown(f"""<div class="ai-box">{result}</div>""", unsafe_allow_html=True)