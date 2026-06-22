import streamlit as st
import json
import os
from pathlib import Path
import time
from PIL import Image
import io
import base64
import fitz  # PyMuPDF
from supabase import create_client, Client

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="✨ English Teacher's Platform ✨",
    page_icon="🌸",
    layout="wide"
)

# ==============================
# CUSTOM CSS + ANIMATIONS
# ==============================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

    .stApp {
        background: linear-gradient(135deg, #ffe6f0 0%, #ffd9e8 50%, #ffe6f0 100%);
        background-size: 400% 400%;
        animation: gradientShift 8s ease infinite;
        font-family: 'Poppins', sans-serif;
    }

    @keyframes gradientShift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    h1, h2, h3 { color: #c2185b !important; }

    /* Boutons animés */
    .stButton > button {
        background: linear-gradient(45deg, #ff69b4, #ff1493);
        color: white;
        border-radius: 25px;
        border: none;
        padding: 12px 25px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255,20,147,0.3);
    }
    .stButton > button:hover {
        transform: scale(1.08) translateY(-3px);
        box-shadow: 0 8px 25px rgba(255,20,147,0.5);
    }
    .stButton > button:active { transform: scale(0.97); }

    /* Course cards */
    .course-card {
        background: white;
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        border: 1px solid #ffc0cb;
        transition: all 0.3s ease;
    }
    .course-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 35px rgba(255,20,147,0.2);
        border-color: #ff69b4;
    }

    /* Animations entrée */
    @keyframes fadeInUp {
        from { transform: translateY(30px); opacity: 0; }
        to   { transform: translateY(0);    opacity: 1; }
    }
    @keyframes fadeInLeft {
        from { transform: translateX(-30px); opacity: 0; }
        to   { transform: translateX(0);     opacity: 1; }
    }
    @keyframes fadeInRight {
        from { transform: translateX(30px); opacity: 0; }
        to   { transform: translateX(0);    opacity: 1; }
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50%       { transform: scale(1.05); }
    }
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50%       { transform: translateY(-10px); }
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to   { transform: rotate(360deg); }
    }
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        25%       { transform: translateY(-15px); }
        75%       { transform: translateY(-7px); }
    }
    @keyframes wiggle {
        0%, 100% { transform: rotate(0deg); }
        25%       { transform: rotate(-10deg); }
        75%       { transform: rotate(10deg); }
    }
    @keyframes rainbow {
        0%   { color: #ff69b4; }
        25%  { color: #ff1493; }
        50%  { color: #c2185b; }
        75%  { color: #ff69b4; }
        100% { color: #ff1493; }
    }
    @keyframes heartbeat {
        0%, 100% { transform: scale(1); }
        14%      { transform: scale(1.3); }
        28%      { transform: scale(1); }
        42%      { transform: scale(1.3); }
        70%      { transform: scale(1); }
    }
    @keyframes oscillate {
        0%, 100% { transform: rotate(-5deg); }
        50%       { transform: rotate(5deg); }
    }
    @keyframes slideDown {
        from { transform: translateY(-20px); opacity: 0; }
        to   { transform: translateY(0);    opacity: 1; }
    }

    /* Ballons */
    @keyframes balloonFloat {
        0%   { transform: translateY(100vh) rotate(-5deg); opacity: 1; }
        80%  { opacity: 1; }
        100% { transform: translateY(-150px) rotate(5deg); opacity: 0; }
    }
    @keyframes balloonSway {
        0%, 100% { margin-left: 0px; }
        25%       { margin-left: 15px; }
        75%       { margin-left: -15px; }
    }

    .fade-in      { animation: fadeInUp   0.6s ease-out; }
    .fade-left    { animation: fadeInLeft  0.6s ease-out; }
    .fade-right   { animation: fadeInRight 0.6s ease-out; }
    .floating     { animation: float  3s ease-in-out infinite; }
    .pulsing      { animation: pulse  2s ease-in-out infinite; }
    .bouncing     { animation: bounce 1.5s ease-in-out infinite; }
    .wiggling     { animation: wiggle 1s ease-in-out infinite; }
    .spinning     { animation: spin 4s linear infinite; }
    .heartbeat    { animation: heartbeat 1.5s ease-in-out infinite; }
    .oscillating  { animation: oscillate 2s ease-in-out infinite; }

    /* Header logos animés - Chacun sa propre animation */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 20px;
        margin: 10px 0 20px 0;
        flex-wrap: wrap;
    }
    .logo-item {
        font-size: 40px;
        display: inline-block;
        cursor: default;
        transition: transform 0.3s ease;
    }
    .logo-item:hover { transform: scale(1.3) rotate(10deg); }
    .logo-1 { animation: float  2.0s ease-in-out infinite; }       /* 📖 flotter */
    .logo-2 { animation: bounce 2.2s ease-in-out infinite; }       /* 📝 rebondir */
    .logo-3 { animation: oscillate 1.8s ease-in-out infinite; }    /* 🎓 osciller */
    .logo-4 { animation: spin 3s linear infinite; }                /* ⭐ tourner */
    .logo-5 { animation: heartbeat 1.5s ease-in-out infinite; }    /* 💖 battre */

    /* Titre animé avec dégradé défilant (shimmer) */
    .main-title {
        text-align: center;
        animation: fadeInUp 0.8s ease-out;
    }
    .main-title h1 {
        background: linear-gradient(90deg, #ff69b4, #c2185b, #ff1493, #ff69b4, #c2185b);
        background-size: 300% 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem !important;
        font-weight: 700;
        animation: shimmer 3s linear infinite;
        display: inline-block;
    }
    @keyframes shimmer {
        0%   { background-position: 0% 50%; }
        100% { background-position: 300% 50%; }
    }
    .subtitle {
        color: #c2185b;
        font-size: 18px;
        animation: pulse 3s ease-in-out infinite;
        display: inline-block;
    }

    /* Sidebar Avatar - Monte et descend doucement */
    .sidebar-avatar {
        font-size: 60px;
        text-align: center;
        animation: float 3s ease-in-out infinite;
        display: block;
    }
    /* Sidebar logos - Pulse en décalé */
    .sidebar-icon-1 { animation: pulse 2s ease-in-out infinite; display: inline-block; margin: 0 3px; }
    .sidebar-icon-2 { animation: pulse 2.3s ease-in-out infinite 0.3s; display: inline-block; margin: 0 3px; }
    .sidebar-icon-3 { animation: pulse 2.6s ease-in-out infinite 0.6s; display: inline-block; margin: 0 3px; }

    .sidebar-title {
        text-align: center;
        background: linear-gradient(45deg, #ff69b4, #ff1493);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        font-size: 1.2rem;
        animation: rainbow 4s ease-in-out infinite;
    }

    /* Ballons container */
    .balloons-container {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9999;
        overflow: hidden;
    }
    .balloon {
        position: absolute;
        bottom: -100px;
        font-size: 50px;
        animation: balloonFloat 4s ease-out forwards,
                   balloonSway  1s ease-in-out infinite;
    }

    /* Success banner animé */
    .success-banner {
        background: linear-gradient(135deg, #ff69b4, #ff1493);
        color: white;
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        font-size: 1.3rem;
        font-weight: bold;
        animation: fadeInUp 0.5s ease-out, pulse 2s ease-in-out infinite 0.5s;
        box-shadow: 0 10px 30px rgba(255,20,147,0.4);
        margin: 10px 0;
    }

    /* Upload zone */
    .stFileUploader {
        border: 3px dashed #ff69b4 !important;
        border-radius: 20px;
        transition: all 0.3s ease;
    }
    .stFileUploader:hover {
        border-color: #ff1493 !important;
        background: rgba(255,105,180,0.05);
        transform: scale(1.01);
    }

    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, #fff0f5, white);
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        border: 2px solid #ffc0cb;
        animation: fadeInUp 0.8s ease-out;
        transition: all 0.3s ease;
    }
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(255,20,147,0.15);
    }
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #ff1493;
        animation: pulse 2s ease-in-out infinite;
        display: inline-block;
    }

    /* Progress bar customisée */
    .stProgress > div > div {
        background: linear-gradient(90deg, #ff69b4, #ff1493) !important;
        border-radius: 10px !important;
    }

    /* Expander animé */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #fff0f5, white) !important;
        border-radius: 15px !important;
        transition: all 0.3s ease !important;
    }
    .streamlit-expanderHeader:hover {
        transform: translateX(5px);
        color: #ff1493 !important;
    }

    /* Spinner personnalisé */
    .stSpinner > div {
        border-color: #ff69b4 transparent transparent transparent !important;
    }

    /* Transitions slides - fondu + légère mise à l'échelle */
    .slide-transition {
        animation: slideFadeScale 0.5s ease-out;
    }
    @keyframes slideFadeScale {
        0%   { opacity: 0; transform: scale(0.95); }
        100% { opacity: 1; transform: scale(1); }
    }

    /* Confetti */
    .confetti-piece {
        position: fixed;
        width: 10px;
        height: 10px;
        top: -10px;
        opacity: 0;
        animation: confettiFall 3s ease-in forwards;
        z-index: 10000;
        pointer-events: none;
    }
    @keyframes confettiFall {
        0%   { opacity: 1; transform: translateY(0) rotate(0deg); }
        100% { opacity: 0; transform: translateY(100vh) rotate(720deg); }
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# BALLONS ANIMATION (HTML + JS)
# ==============================
def show_balloons_animation():
    """Affiche des ballons qui volent vers le haut avec animation."""
    balloons_html = """
    <div class="balloons-container" id="balloonsContainer">
        <div class="balloon" style="left:5%;  animation-delay:0.0s; animation-duration:3.5s;">🎈</div>
        <div class="balloon" style="left:15%; animation-delay:0.2s; animation-duration:4.0s;">🌸</div>
        <div class="balloon" style="left:25%; animation-delay:0.1s; animation-duration:3.8s;">🎈</div>
        <div class="balloon" style="left:35%; animation-delay:0.3s; animation-duration:4.2s;">💖</div>
        <div class="balloon" style="left:45%; animation-delay:0.0s; animation-duration:3.6s;">🎈</div>
        <div class="balloon" style="left:55%; animation-delay:0.4s; animation-duration:4.1s;">🌸</div>
        <div class="balloon" style="left:65%; animation-delay:0.1s; animation-duration:3.9s;">🎈</div>
        <div class="balloon" style="left:75%; animation-delay:0.2s; animation-duration:4.3s;">💖</div>
        <div class="balloon" style="left:85%; animation-delay:0.3s; animation-duration:3.7s;">🎈</div>
        <div class="balloon" style="left:92%; animation-delay:0.1s; animation-duration:4.0s;">✨</div>
        <div class="balloon" style="left:10%; animation-delay:0.5s; animation-duration:3.5s;">🎊</div>
        <div class="balloon" style="left:50%; animation-delay:0.6s; animation-duration:4.5s;">🎉</div>
        <div class="balloon" style="left:80%; animation-delay:0.4s; animation-duration:3.8s;">💕</div>
    </div>
    <script>
        setTimeout(function() {
            var container = document.getElementById('balloonsContainer');
            if (container) container.remove();
        }, 5000);
    </script>
    """
    st.markdown(balloons_html, unsafe_allow_html=True)
    st.balloons()

# ==============================
# CONFETTI ANIMATION
# ==============================
def show_confetti():
    """Affiche des confetti qui tombent."""
    confetti_html = """
    <script>
        (function() {
            const colors = ['#ff69b4','#ff1493','#c2185b','#ffc0cb','#ffe6f0','#ffb6c1','#ff6b6b','#ffd93d'];
            for (let i = 0; i < 50; i++) {
                setTimeout(function() {
                    var c = document.createElement('div');
                    c.className = 'confetti-piece';
                    c.style.left = Math.random() * 100 + 'vw';
                    c.style.background = colors[Math.floor(Math.random() * colors.length)];
                    c.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
                    c.style.width = (6 + Math.random() * 10) + 'px';
                    c.style.height = (6 + Math.random() * 10) + 'px';
                    c.style.animationDuration = (2 + Math.random() * 2) + 's';
                    c.style.animationDelay = (Math.random() * 0.5) + 's';
                    document.body.appendChild(c);
                    setTimeout(function() { c.remove(); }, 4000);
                }, i * 60);
            }
        })();
    </script>
    """
    st.markdown(confetti_html, unsafe_allow_html=True)

# ==============================
# SUPABASE
# ==============================
BUCKET = "courses"

@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

def load_metadata() -> dict:
    try:
        rows = get_supabase().table("courses").select("*").execute().data
        return {r["id"]: r for r in rows}
    except Exception as e:
        st.error(f"❌ Cannot load courses: {e}")
        return {}

def save_course(course_id: str, data: dict):
    get_supabase().table("courses").upsert({"id": course_id, **data}).execute()

def remove_course(course_id: str):
    get_supabase().table("courses").delete().eq("id", course_id).execute()

def upload_pdf(file_bytes: bytes, storage_path: str):
    get_supabase().storage.from_(BUCKET).upload(
        storage_path, file_bytes,
        {"content-type": "application/pdf", "upsert": "true"}
    )

def download_pdf(storage_path: str) -> bytes:
    return get_supabase().storage.from_(BUCKET).download(storage_path)

def delete_pdf(storage_path: str):
    get_supabase().storage.from_(BUCKET).remove([storage_path])

# ==============================
# PDF → BASE64 IMAGES
# ==============================
def pdf_bytes_to_base64_images(pdf_bytes: bytes) -> list:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images_b64 = []
    for page in doc:
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        if img.width > 1200:
            ratio = 1200 / img.width
            img = img.resize((1200, int(img.height * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        images_b64.append(base64.b64encode(buf.getvalue()).decode())
    doc.close()
    return images_b64

# ==============================
# HTML VIEWER
# ==============================
def create_html_viewer(images_base64, current_page, total_pages, course_title):
    current_img = images_base64[current_page]
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            * {{ margin:0; padding:0; box-sizing:border-box; }}
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background: linear-gradient(135deg, #ffe6f0 0%, #ffd9e8 100%);
                padding: 20px;
            }}
            .presentation-container {{
                max-width: 1100px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
                animation: fadeIn 0.5s ease-out;
            }}
            @keyframes fadeIn {{
                from {{ opacity:0; transform:translateY(20px); }}
                to   {{ opacity:1; transform:translateY(0); }}
            }}
            .presentation-container:fullscreen,
            .presentation-container:-webkit-full-screen,
            .presentation-container:-moz-full-screen {{
                max-width:100%; width:100vw; height:100vh;
                border-radius:0; padding:20px; overflow-y:auto;
                background:white; display:flex; flex-direction:column;
                justify-content:center;
            }}
            .fullscreen-top {{
                display:flex; justify-content:flex-end; margin-bottom:15px;
            }}
            .btn-fullscreen {{
                background: linear-gradient(45deg, #2196F3, #1976D2);
                color:white; border:none; border-radius:25px;
                padding:12px 30px; font-weight:bold; cursor:pointer;
                transition:all 0.3s ease; font-size:16px;
                box-shadow:0 4px 15px rgba(33,150,243,0.3);
                animation: pulse 2s ease-in-out infinite;
            }}
            @keyframes pulse {{
                0%,100% {{ box-shadow:0 4px 15px rgba(33,150,243,0.3); }}
                50%      {{ box-shadow:0 4px 25px rgba(33,150,243,0.6); }}
            }}
            .btn-fullscreen:hover {{
                transform:scale(1.08) translateY(-3px);
                background:linear-gradient(45deg,#1976D2,#0D47A1);
            }}
            .header {{
                display:flex; justify-content:space-between;
                align-items:center; margin-bottom:15px;
                flex-wrap:wrap; gap:10px;
            }}
            h1 {{
                color:#c2185b; font-size:22px; margin:0;
                background:linear-gradient(45deg,#ff69b4,#c2185b);
                -webkit-background-clip:text;
                -webkit-text-fill-color:transparent;
            }}
            .page-info {{
                color:#c2185b; font-weight:bold; font-size:15px;
                background:#ffe6f0; padding:6px 16px; border-radius:20px;
                border:2px solid #ffc0cb;
            }}
            .progress-bar {{
                width:100%; height:8px; background:#f0f0f0;
                border-radius:4px; overflow:hidden; margin:10px 0 20px 0;
            }}
            .progress-fill {{
                width:{((current_page + 1) / total_pages) * 100}%;
                height:100%;
                background:linear-gradient(90deg, #ff69b4, #ff1493);
                transition:width 0.4s ease;
                border-radius:4px;
            }}
            .image-wrapper {{
                width:100%; display:flex; justify-content:center;
                align-items:center; min-height:400px;
                background:#fafafa; border-radius:12px;
                padding:10px; margin-bottom:20px;
                transition: all 0.3s ease;
            }}
            .page-image {{
                max-width:100%; max-height:70vh;
                object-fit:contain; border-radius:8px;
                box-shadow:0 4px 15px rgba(0,0,0,0.08);
                user-select:none;
                transition: opacity 0.3s ease, transform 0.3s ease;
            }}
            .page-image.changing {{ opacity: 0; transform: scale(0.95); }}
            .nav-buttons {{
                display:flex; justify-content:center;
                gap:15px; margin:15px 0 0 0; flex-wrap:wrap;
            }}
            .btn-nav {{
                background:linear-gradient(45deg, #ff69b4, #ff1493);
                color:white; border:none; border-radius:25px;
                padding:12px 30px; font-weight:bold; cursor:pointer;
                transition:all 0.3s ease; font-size:16px; min-width:140px;
                box-shadow:0 4px 15px rgba(255,20,147,0.3);
            }}
            .btn-nav:hover:not(:disabled) {{
                transform:scale(1.08) translateY(-3px);
                box-shadow:0 8px 25px rgba(255,20,147,0.5);
            }}
            .btn-nav:active:not(:disabled) {{ transform:scale(0.97); }}
            .btn-nav:disabled {{ opacity:0.4; cursor:not-allowed; transform:none; }}

            /* Transition de slide */
            .slide-transition {{
                animation: slideFadeScale 0.5s ease-out;
            }}
            @keyframes slideFadeScale {{
                0%   {{ opacity: 0; transform: scale(0.95); }}
                100% {{ opacity: 1; transform: scale(1); }}
            }}

            @media (max-width:768px) {{
                body {{ padding:10px; }}
                .presentation-container {{ padding:15px; }}
                h1 {{ font-size:18px; }}
                .btn-nav {{ padding:10px 20px; font-size:14px; min-width:100px; }}
                .btn-fullscreen {{ font-size:14px; padding:10px 20px; }}
                .image-wrapper {{ min-height:250px; }}
            }}
        </style>
    </head>
    <body>
        <div class="presentation-container" id="presentationContainer">
            <div class="fullscreen-top">
                <button class="btn-fullscreen" id="fullscreenBtn">
                    🖥️ PLEIN ÉCRAN
                </button>
            </div>
            <div class="header">
                <h1>📖 {course_title}</h1>
                <div class="page-info" id="pageInfo">
                    Page {current_page + 1} / {total_pages}
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="image-wrapper">
                <img id="pageImage" class="page-image slide-transition"
                     src="data:image/png;base64,{current_img}"
                     alt="Page {current_page + 1}" />
            </div>
            <div class="nav-buttons">
                <button class="btn-nav" id="prevBtn" {"disabled" if current_page == 0 else ""}>
                    ◀◀ PRÉCÉDENT
                </button>
                <button class="btn-nav" id="nextBtn" {"disabled" if current_page == total_pages - 1 else ""}>
                    SUIVANT ▶▶
                </button>
            </div>
        </div>

        <script>
            const imagesBase64 = {json.dumps(images_base64)};
            let currentPage   = {current_page};
            const totalPages  = {total_pages};
            const pageImage   = document.getElementById('pageImage');
            const pageInfo    = document.getElementById('pageInfo');
            const progressFill= document.getElementById('progressFill');
            const prevBtn     = document.getElementById('prevBtn');
            const nextBtn     = document.getElementById('nextBtn');
            const container   = document.getElementById('presentationContainer');

            function updatePage(index) {{
                if (index < 0 || index >= totalPages) return;

                // Animation transition - fondu + mise à l'échelle
                pageImage.classList.remove('slide-transition');
                pageImage.style.opacity = '0';
                pageImage.style.transform = 'scale(0.95)';

                setTimeout(function() {{
                    currentPage = index;
                    pageImage.src = 'data:image/png;base64,' + imagesBase64[index];
                    pageInfo.textContent = 'Page ' + (index+1) + ' / ' + totalPages;
                    progressFill.style.width = ((index+1)/totalPages*100) + '%';
                    prevBtn.disabled = (index === 0);
                    nextBtn.disabled = (index === totalPages-1);

                    // Déclencher l'animation d'entrée
                    pageImage.style.opacity = '1';
                    pageImage.style.transform = 'scale(1)';
                    pageImage.classList.add('slide-transition');

                    // Confetti à la dernière page
                    if (index === totalPages - 1) {{
                        launchConfetti();
                    }}
                }}, 200);
            }}

            function launchConfetti() {{
                const colors = ['#ff69b4','#ff1493','#c2185b','#ffc0cb','#ffe6f0','#ffb6c1','#ff6b6b','#ffd93d'];
                for (let i = 0; i < 50; i++) {{
                    setTimeout(function() {{
                        var c = document.createElement('div');
                        c.className = 'confetti-piece';
                        c.style.left = Math.random() * 100 + 'vw';
                        c.style.background = colors[Math.floor(Math.random() * colors.length)];
                        c.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
                        c.style.width = (6 + Math.random() * 10) + 'px';
                        c.style.height = (6 + Math.random() * 10) + 'px';
                        c.style.animationDuration = (2 + Math.random() * 2) + 's';
                        c.style.animationDelay = (Math.random() * 0.5) + 's';
                        document.body.appendChild(c);
                        setTimeout(function() {{ c.remove(); }}, 4000);
                    }}, i * 60);
                }}
            }}

            prevBtn.addEventListener('click', function() {{
                if (currentPage > 0) updatePage(currentPage - 1);
            }});
            nextBtn.addEventListener('click', function() {{
                if (currentPage < totalPages-1) updatePage(currentPage + 1);
            }});
            document.addEventListener('keydown', function(e) {{
                if (e.key==='ArrowLeft'  && currentPage>0)            {{ updatePage(currentPage-1); e.preventDefault(); }}
                if (e.key==='ArrowRight' && currentPage<totalPages-1)  {{ updatePage(currentPage+1); e.preventDefault(); }}
            }});

            document.getElementById('fullscreenBtn').addEventListener('click', function() {{
                if (!document.fullscreenElement && !document.webkitFullscreenElement &&
                    !document.mozFullScreenElement) {{
                    (container.requestFullscreen || container.webkitRequestFullscreen ||
                     container.msRequestFullscreen || container.mozRequestFullScreen).call(container);
                }} else {{
                    (document.exitFullscreen || document.webkitExitFullscreen ||
                     document.msExitFullscreen || document.mozCancelFullScreen).call(document);
                }}
            }});
            document.addEventListener('fullscreenchange', function() {{
                container.style.maxWidth = document.fullscreenElement ? '100%' : '1100px';
            }});
        </script>
    </body>
    </html>
    """
    return html_code

# ==============================
# DISPLAY PRESENTATION
# ==============================
def display_presentation(course):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)

    if st.button("◀ Back to Courses"):
        st.session_state['viewing_course'] = None
        for k in ['pdf_images', 'current_pdf_key', 'current_page']:
            st.session_state.pop(k, None)
        st.rerun()

    st.markdown(f"""
        <div style="text-align:center;" class="fade-in">
            <h2>📖 {course['title']}</h2>
            <p style="color:#c2185b;">
                <span class="floating" style="display:inline-block;">🎯</span>
                Level {course['level']} &nbsp;|&nbsp; 📅 {course['upload_date']}
            </p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    course_key = course["id"]

    if 'pdf_images' not in st.session_state or \
       st.session_state.get('current_pdf_key') != course_key:
        with st.spinner("🔄 Chargement du cours…"):
            try:
                pdf_bytes  = download_pdf(course["storage_path"])
                images_b64 = pdf_bytes_to_base64_images(pdf_bytes)
                st.session_state.pdf_images      = images_b64
                st.session_state.current_pdf_key = course_key
                st.session_state.current_page    = 0
            except Exception as e:
                st.error(f"❌ Impossible d'afficher ce PDF : {e}")
                return

    images_base64 = st.session_state.pdf_images
    total_pages   = len(images_base64)

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown(
            f"<h3 style='text-align:center;color:#c2185b;'>"
            f"📄 Page {st.session_state.current_page + 1} / {total_pages}</h3>",
            unsafe_allow_html=True
        )
        st.progress((st.session_state.current_page + 1) / total_pages)
    st.markdown("---")

    html_viewer = create_html_viewer(
        images_base64,
        st.session_state.current_page,
        total_pages,
        course['title']
    )
    st.components.v1.html(html_viewer, height=780, scrolling=True)

    with st.expander("📥 Télécharger le PDF original", expanded=False):
        pdf_bytes = download_pdf(course["storage_path"])
        st.download_button(
            "Télécharger le fichier PDF",
            data=pdf_bytes,
            file_name=course["filename"],
            mime="application/pdf"
        )

    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# MAIN
# ==============================
def main():
    if 'viewing_course' not in st.session_state:
        st.session_state.viewing_course = None

    # Header avec titre animé (shimmer) et logos avec animations individuelles
    st.markdown("""
        <div class="main-title">
            <h1>🌸
