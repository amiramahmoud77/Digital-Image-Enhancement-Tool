import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
import matplotlib.pyplot as plt

# Custom CSS for Memebase UI
st.markdown("""
<style>
.main {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);}
.stButton > button {background: linear-gradient(45deg, #FF6B6B, #4ECDC4); color: white; border-radius: 50px; font-weight: bold;}
.stSlider > div > div > div {background: #4ECDC4 !important;}
</style>
""", unsafe_allow_html=True)

st.set_page_config(layout="wide")
st.title("🖼️ Digital Image Enhancement Tool")

# Defaults for stronger effects
DEFAULT_ALPHA = 2.5  # Stronger contrast
DEFAULT_BETA = 10
DEFAULT_GAMMA = 0.6  # Brightens dark areas
FILTERS = ["Histogram Equalization", "Contrast Stretching", "Gamma Correction", "Sharpening Filter", "Smoothing Filter"]

# Session state
if 'filter_choice' not in st.session_state:
    st.session_state.filter_choice = FILTERS[0]
if 'alpha' not in st.session_state:
    st.session_state.alpha = DEFAULT_ALPHA
if 'beta' not in st.session_state:
    st.session_state.beta = DEFAULT_BETA
if 'gamma' not in st.session_state:
    st.session_state.gamma = DEFAULT_GAMMA
if 'intensity' not in st.session_state:
    st.session_state.intensity = 1.0

# Sidebar
st.sidebar.header("⚙️ Settings")
batch_mode = st.sidebar.checkbox("Batch Mode", False)

# Callback for filter change
def on_filter_change():
    st.rerun()

uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
if uploaded_file is None:
    st.info("No image? Using a default dark image for demo.")
    # Default dark image for testing
    image = np.full((300, 400, 3), 50, dtype=np.uint8)  # Dark gray
else:
    image = np.array(Image.open(uploaded_file))
    if len(image.shape) == 3 and image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

original_contrast = np.std(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))

col1, col2 = st.columns(2)
with col1:
    st.subheader("📸 Original")
    st.image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), use_column_width=True)

# Filter Selection
st.session_state.filter_choice = st.selectbox("Select Filter:", FILTERS, key="filter_key", on_change=on_filter_change)
filter_choice = st.session_state.filter_choice

# Intensity Slider (Stronger Effects!)
st.session_state.intensity = st.slider("Intensity (Strength)", 0.5, 2.0, 1.0, key="intensity_key")

# Dynamic Parameters (Live Rerun!)
if filter_choice == "Contrast Stretching":
    st.session_state.alpha = st.slider("Alpha", 0.5, 3.0, DEFAULT_ALPHA, key="alpha_key")
    st.session_state.beta = st.slider("Beta", -50, 50, DEFAULT_BETA, key="beta_key")
elif filter_choice == "Gamma Correction":
    st.session_state.gamma = st.slider("Gamma", 0.5, 2.5, DEFAULT_GAMMA, key="gamma_key")

# Live Preview (Changes instantly!)
intensity = st.session_state.intensity
preview_processed = image.copy()
if filter_choice == "Contrast Stretching":
    preview_processed = cv2.convertScaleAbs(preview_processed, alpha=st.session_state.alpha * intensity, beta=st.session_state.beta)
elif filter_choice == "Gamma Correction":
    inv_gamma = 1.0 / (st.session_state.gamma * intensity)
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    preview_processed = cv2.LUT(preview_processed, table)
# Add more for other filters if needed

with col2:
    st.subheader("👀 Live Preview")
    st.image(cv2.cvtColor(preview_processed, cv2.COLOR_BGR2RGB), use_column_width=True)

# Apply Button
if st.button("🚀 Apply Filter"):
    progress = st.progress(0)
    progress.progress(0.5)
    processed = image.copy()
    intensity = st.session_state.intensity
    if filter_choice == "Histogram Equalization":
        lab = cv2.cvtColor(processed, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0 * intensity, tileGridSize=(8,8))  # Stronger
        cl = clahe.apply(l)
        processed = cv2.merge((cl, a, b))
        processed = cv2.cvtColor(processed, cv2.COLOR_LAB2BGR)
    elif filter_choice == "Contrast Stretching":
        processed = cv2.convertScaleAbs(processed, alpha=st.session_state.alpha * intensity, beta=st.session_state.beta)
    elif filter_choice == "Gamma Correction":
        inv_gamma = 1.0 / (st.session_state.gamma * intensity)
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        processed = cv2.LUT(processed, table)
    elif filter_choice == "Sharpening Filter":
        kernel = np.array([[-1,-1,-1], [-1,9 * intensity,-1], [-1,-1,-1]])  # Stronger kernel
        processed = cv2.filter2D(processed, -1, kernel)
    elif filter_choice == "Smoothing Filter":
        processed = cv2.GaussianBlur(processed, (5,5), 0 * intensity)  # Adjust sigma

    progress.progress(1.0)

    processed_contrast = np.std(cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY))
    improvement = ((processed_contrast - original_contrast) / original_contrast * 100)
    st.success(f"✨ Contrast Improvement: {improvement:.1f}% (with {intensity}x Intensity!)")

    st.subheader("Processed (Final)")
    st.image(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB), use_column_width=True)

    # Histogram
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    gray_orig = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray_proc = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
    ax[0].hist(gray_orig.ravel(), bins=256, color='blue')
    ax[0].set_title("Original Histogram")
    ax[1].hist(gray_proc.ravel(), bins=256, color='green')
    ax[1].set_title("Processed Histogram")
    st.pyplot(fig)

    st.download_button("💾 Download", cv2.imencode('.jpg', processed)[1].tobytes(), "processed.jpg")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: white;'>Built with ❤️ for Digital Image Processing</p>", unsafe_allow_html=True)