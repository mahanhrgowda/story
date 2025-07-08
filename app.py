```python
import streamlit as st
import pandas as pd
from phonemizer import phonemize
from phonemizer.backend import EspeakBackend
import requests
import re

# Initialize Streamlit app
st.title("Phoneme to Chakra Story Generator")
st.markdown("Enter an English name to discover its phonemes, associated chakras, and a mystical story set in ancient India.")

# Input for name
name = st.text_input("Enter a name:", placeholder="e.g., Mahaan")

# Input for xAI API key (use Streamlit secrets for deployment)
api_key = st.secrets.get("XAI_API_KEY", "")
if not api_key:
    st.warning("Please enter an xAI API key. For deployment, store it in Streamlit secrets.")

# Load phoneme-chakra mapping from CSV
@st.cache_data
def load_phoneme_data():
    try:
        df = pd.read_csv("phoneme_chakra_mapping.csv")
        return df.set_index("IPA")["Chakra"].to_dict()
    except FileNotFoundError:
        st.error("phoneme_chakra_mapping.csv not found. Ensure it's in the repository.")
        return {}

phoneme_chakra_map = load_phoneme_data()

# Function to normalize phonemes for matching
def normalize_phoneme(phoneme):
    return re.sub(r"[ˈˌː]", "", phoneme).strip()

# Function to extract phonemes
def get_phonemes(name):
    try:
        backend = EspeakBackend('en-us')
        phonemes = phonemize(name, language='en-us', backend='espeak', strip=True, with_stress=False)
        return phonemes.split()
    except Exception as e:
        st.error(f"Error extracting phonemes: {e}")
        return []

# Function to map phonemes to chakras
def map_phonemes_to_chakras(phonemes):
    chakras = []
    matched_phonemes = []
    for phoneme in phonemes:
        norm_phoneme = normalize_phoneme(phoneme)
        if norm_phoneme in phoneme_chakra_map:
            chakras.append(phoneme_chakra_map[norm_phoneme])
            matched_phonemes.append((phoneme, norm_phoneme, phoneme_chakra_map[norm_phoneme]))
        else:
            matched_phonemes.append((phoneme, norm_phoneme, "Not found"))
    return matched_phonemes, chakras

# Function to generate story using xAI API
def generate_story(name, chakras, api_key):
    if not chakras:
        return "No chakras found to generate a story."
    if not api_key:
        return "Please provide a valid xAI API key."

    unique_chakras = list(set(chakras))
    chakra_desc = {
        "Muladhara": "root chakra, symbolizing grounding and stability",
        "Svadhisthana": "sacral chakra, representing creativity and emotion",
        "Manipura": "solar plexus chakra, embodying power and will",
        "Anahata": "heart chakra, signifying love and compassion",
        "Vishuddha": "throat chakra, associated with communication and truth",
        "Ajna": "third eye chakra, linked to intuition and wisdom",
        "Sahasrara": "crown chakra, connecting to divine consciousness"
    }

    prompt = f"""
    Write a mystical story (500-1000 words) set in the ancient Indian mythological age, during the era of gods, sages, and cosmic battles. The story should center on the protagonist, {name or 'a sage'}, who embarks on a spiritual quest guided by the chakras: {', '.join(unique_chakras)}. Each chakra influences the narrative, reflecting its symbolic meaning ({'; '.join([f'{k}: {chakra_desc[k]}' for k in unique_chakras if k in chakra_desc])}). Incorporate Indian mythological elements (e.g., deities like Vishnu, Shiva, or Devi, sacred rivers, or ancient forests). The story should be vivid, enchanting, and deeply spiritual, with a tone of awe and reverence.
    """

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "grok-3",
            "prompt": prompt,
            "max_tokens": 2000,
            "temperature": 0.7
        }
        response = requests.post("https://api.x.ai/v1/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["text"].strip()
    except Exception as e:
        return f"Error generating story: {e}"

# Process input and generate output
if st.button("Generate Story") and name:
    with st.spinner("Processing..."):
        phonemes = get_phonemes(name)
        if phonemes:
            st.subheader("Phonemes Extracted")
            st.write(", ".join(phonemes))

            matched_phonemes, chakras = map_phonemes_to_chakras(phonemes)
            st.subheader("Phoneme to Chakra Mapping")
            for phoneme, norm_phoneme, chakra in matched_phonemes:
                st.write(f"Phoneme: {phoneme} (Normalized: {norm_phoneme}) → Chakra: {chakra}")

            st.subheader("Associated Chakras")
            if chakras:
                st.write(", ".join(chakras))
            else:
                st.warning("No chakras matched. Story generation may be limited.")

            st.subheader("Mystical Story")
            story = generate_story(name, chakras, api_key)
            st.markdown(story)
        else:
            st.error("Could not extract phonemes. Please try another name.")
```
