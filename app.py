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
# CUSTOM CSS + ANIMATIONS (Version corrigée)
# ==============================
st.markdown("""
<style>
    /* Reset et fond */
    .stApp {
        background: linear-gradient(135deg, #ffe6f0 0%, #ffd9e8 50%, #ffe6f0 100%);
        background-size: 400% 400%;
        animation: gradientShift 8s ease infinite;
    }

    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* ===== TITRE SHIMMER ===== */
    .shimmer-title {
        font-size: 2.8rem !important;
        font-weight: 700;
        background: linear-gradient(90deg, #ff69b4, #c2185b, #ff1493, #ff69b4, #c2185b);
        background-size: 300% 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: shimmer 3s linear infinite;
        display: inline-block;
        text-align: center;
        padding: 10px;
    }

    @keyframes shimmer {
        0% { background-position: 0% 50%; }
        100% { background-position: 300% 50%; }
    }

    /* ===== LOGOS AVEC LEURS PROPRES ANIMATIONS ===== */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 30px;
        margin: 15px 0 25px 0;
        flex-wrap: wrap;
        padding: 15px;
        background: rgba(255,255,255,0.3);
        border-radius: 50px;
        backdrop-filter: blur(5px);
    }

    .logo-item {
        font-size: 50px;
        display: inline-block;
        cursor: default;
        transition: transform 0.3s ease;
        padding: 5px;
    }

    .logo-item:hover {
        transform: scale(1.5) rotate(15deg) !important;
    }

    /* Chaque logo a sa propre animation */
    .logo-float { animation: floatAnim 2.5s ease-in-out infinite; }
    .logo-bounce { animation: bounceAnim 2s ease-in-out infinite; }
    .logo-oscillate { animation: oscillateAnim 1.8s ease-in-out infinite; }
    .logo-spin { animation: spinAnim 4s linear infinite; }
    .logo-heartbeat { animation: heartbeatAnim 1.5s ease-in-out infinite; }

    @keyframes floatAnim {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }

    @keyframes bounceAnim {
        0%, 100% { transform: translateY(0); }
        25% { transform: translateY(-25px); }
        75% { transform: translateY(-10px); }
    }

    @keyframes oscillateAnim {
        0%, 100% { transform: rotate(-10deg); }
        50% { transform: rotate(10deg); }
    }

    @keyframes spinAnim {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    @keyframes heartbeatAnim {
        0%, 100% { transform: scale(1); }
        14% { transform: scale(1.4); }
        28% { transform: scale(1); }
        42% { transform: scale(1.4); }
        70% { transform: scale(1); }
    }

    /* ===== SIDEBAR ===== */
    .sidebar-avatar {
        font-size: 70px;
        text-align: center;
        animation: floatAnim 3s ease-in-out infinite;
        display: block;
        padding: 15px;
    }

    .sidebar-icons {
        text-align: center;
        padding: 10px;
    }

    .sidebar-icon {
        font-size: 30px;
        display: inline-block;
        margin: 0 8px;
    }

    .icon-pulse-1 { animation: pulseAnim 2s ease-in-out infinite; }
    .icon-pulse-2 { animation: pulseAnim 2.3s ease-in-out infinite 0.3s; }
    .icon-pulse-3 { animation: pulseAnim 2.6s ease-in-out infinite 0.6s; }

    @keyframes pulseAnim {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.3); }
    }

    .sidebar-title {
        text-align: center;
        font-weight: 700;
        font-size: 1.3rem;
        animation: rainbowAnim 4s ease-in-out infinite;
        padding: 10px;
        background: linear-gradient(45deg, #ff69b4, #ff1493);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    @keyframes rainbowAnim {
        0% { filter: hue-rotate(0deg); }
        100% { filter: hue-rotate(360deg); }
    }

    /* ===== BOUTONS ===== */
    .stButton > button {
        background: linear-gradient(45deg, #ff69b4, #ff1493) !important;
        color: white !important;
        border-radius: 25px !important;
        border: none !important;
        padding: 12px 25px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        animation: btnGlow 2s ease-in-out infinite !important;
    }

    @keyframes btnGlow {
        0%, 100% { box-shadow: 0 4px 15px rgba(255,20,147,0.3); }
        50% { box-shadow: 0 4px 30px rgba(255,20,147,0.6); }
    }

    .stButton > button:hover {
        transform: scale(1.08) translateY(-3px) !important;
        box-shadow: 0 8px 30px rgba(255,20,147,0.7) !important;
    }

    /* ===== COURSE CARDS ===== */
    .course-card {
        background: white;
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        border: 1px solid #ffc0cb;
        transition: all 0.3s ease;
        animation: cardSlideIn 0.6s ease-out;
    }

    @keyframes cardSlideIn {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .course-card:hover {
        transform: translateY(-10px) !important;
        box-shadow: 0 15px 40px rgba(255,20,147,0.25) !important;
        border-color: #ff69b4 !important;
    }

    /* ===== SUCCESS BANNER ===== */
    .success-banner {
        background: linear-gradient(135deg, #ff69b4, #ff1493);
        color: white;
        border-radius: 20px;
        padding: 25px;
        text-align: center;
        font-size: 1.4rem;
        font-weight: bold;
        animation: bannerIn 0.5s ease-out, bannerPulse 2s ease-in-out infinite 0.5s;
        box-shadow: 0 10px 30px rgba(255,20,147,0.4);
        margin: 15px 0;
    }

    @keyframes bannerIn {
        from { opacity: 0; transform: scale(0.8) translateY(30px); }
        to { opacity: 1; transform: scale(1) translateY(0); }
    }

    @keyframes bannerPulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }

    /* ===== STAT CARDS ===== */
    .stat-card {
        background: linear-gradient(135deg, #fff0f5, white);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        border: 2px solid #ffc0cb;
        transition: all 0.3s ease;
        animation: statFadeIn 0.8s ease-out;
    }

    @keyframes statFadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(255,20,147,0.15);
    }

    .stat-number {
        font-size: 2.2rem;
        font-weight: 700;
        color: #ff1493;
        animation: numberPulse 2s ease-in-out infinite;
        display: inline-block;
    }

    @keyframes numberPulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }

    /* ===== SUBTITLE ===== */
    .subtitle {
        color: #c2185b;
        font-size: 18px;
        animation: subtitlePulse 3s ease-in-out infinite;
        display: inline-block;
    }

    @keyframes subtitlePulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* ===== BALLONS ===== */
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

    @keyframes balloonFloat {
        0% { transform: translateY(100vh) rotate(-5deg) scale(0.5); opacity: 1; }
        100% { transform: translateY(-150px) rotate(5deg) scale(1); opacity: 0; }
    }

    @keyframes balloonSway {
        0%, 100% { margin-left: 0px; }
        25% { margin-left: 25px; }
        75% { margin-left: -25px; }
    }

    .balloon {
        position: absolute;
        bottom: -100px;
        font-size: 55px;
        animation: balloonFloat 4.5s ease-out forwards,
                   balloonSway 1.5s ease-in-out infinite;
    }

    /* ===== CONFETTI ===== */
    .confetti-piece {
        position: fixed;
        width: 12px;
        height: 12px;
        top: -10px;
        opacity: 0;
        animation: confettiFall 3.5s ease-in forwards;
        z-index: 10000;
        pointer-events: none;
    }

    @keyframes confettiFall {
        0% { opacity: 1; transform: translateY(0) rotate(0deg) scale(1); }
        100% { opacity: 0; transform: translateY(110vh) rotate(720deg) scale(0.5); }
    }

    /* ===== TRANSITIONS SLIDES ===== */
    .slide-transition {
        animation: slideFadeScale 0.6s ease-out;
    }

    @keyframes slideFadeScale {
        0% { opacity: 0; transform: scale(0.92); }
        100% { opacity: 1; transform: scale(1); }
    }

    /* ===== UPLOAD ZONE ===== */
    .stFileUploader {
        border: 3px dashed #ff69b4 !important;
        border-radius: 20px !important;
        transition: all 0.3s ease !important;
    }

    .stFileUploader:hover {
        border-color: #ff1493 !important;
        background: rgba(255,105,180,0.05) !important;
        transform: scale(1.02) !important;
    }

    /* ===== PROGRESS BAR ===== */
    .stProgress > div > div {
        background: linear-gradient(90deg, #ff69b4, #ff1493) !important;
        border-radius: 10px !important;
    }

    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #fff0f5, white) !important;
        border-radius: 15px !important;
        transition: all 0.3s ease !important;
    }

    .streamlit-expanderHeader:hover {
        transform: translateX(8px) !important;
        color: #ff1493 !important;
    }

    /* ===== AUTRES ANIMATIONS UTILITAIRES ===== */
    .fade-in { animation: fadeInUp 0.6s ease-out; }
    .fade-left { animation: fadeInLeft 0.6s ease-out; }
    .fade-right { animation: fadeInRight 0.6s ease-out; }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes fadeInLeft {
        from { opacity: 0; transform: translateX(-30px); }
        to { opacity: 1; transform: translateX(0); }
    }

    @keyframes fadeInRight {
        from { opacity: 0; transform: translateX(30px); }
        to { opacity: 1; transform: translateX(0); }
    }

    .floating { animation: floatAnim 3s ease-in-out infinite; }
    .pulsing { animation: pulseAnim 2s ease-in-out infinite; }
    .bouncing { animation: bounceAnim 1.5s ease-in-out infinite; }
    .heartbeat { animation: heartbeatAnim 1.5s ease-in-out infinite; }
    .spinning { animation: spinAnim 4s linear infinite; }
</style>
""", unsafe_allow_html=True)

# ==============================
# BALLONS ANIMATION
# ==============================
def show_balloons_animation():
    balloons_html = """
    <div class="balloons-container" id="balloonsContainer">
        <div class="balloon" style="left:5%; animation-delay:0.0s; animation-duration:4.0s;">🎈</div>
        <div class="balloon" style="left:15%; animation-delay:0.2s; animation-duration:4.5s;">🌸</div>
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
# CONFETTI
# ==============================
def show_confetti():
    confetti_html = """
    <script>
        (function() {
            const colors = ['#ff69b4','#ff1493','#c2185b','#ffc0cb','#ffe6f0','#ffb6c1','#ff6b6b','#ffd93d','#ff9ff3','#54a0ff'];
            for (let i = 0; i < 60; i++) {
                setTimeout(function() {
                    var c = document.createElement('div');
                    c.className = 'confetti-piece';
                    c.style.left = Math.random() * 100 + 'vw';
                    c.style.background = colors[Math.floor(Math.random() * colors.length)];
                    c.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
                    c.style.width = (6 + Math.random() * 12) + 'px';
                    c.style.height = (6 + Math.random() * 12) + 'px';
                    c.style.animationDuration = (2 + Math.random() * 2.5) + 's';
                    c.style.animationDelay = (Math.random() * 0.5) + 's';
                    document.body.appendChild(c);
                    setTimeout(function() { c.remove(); }, 4000);
                }, i * 70);
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
                animation: btnPulse 2s ease-in-out infinite;
            }}
            @keyframes btnPulse {{
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
                transition: opacity 0.4s ease, transform 0.4s ease;
            }}
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

            .slide-transition {{
                animation: slideFadeScale 0.5s ease-out;
            }}
            @keyframes slideFadeScale {{
                0%   {{ opacity: 0; transform: scale(0.92); }}
                100% {{ opacity: 1; transform: scale(1); }}
            }}

            .confetti-piece {{
                position: fixed;
                width: 10px;
                height: 10px;
                top: -10px;
                opacity: 0;
                animation: confettiFall 3s ease-in forwards;
                z-index: 10000;
                pointer-events: none;
            }}
            @keyframes confettiFall {{
                0%   {{ opacity: 1; transform: translateY(0) rotate(0deg); }}
                100% {{ opacity: 0; transform: translateY(100vh) rotate(720deg); }}
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

                pageImage.classList.remove('slide-transition');
                pageImage.style.opacity = '0';
                pageImage.style.transform = 'scale(0.92)';

                setTimeout(function() {{
                    currentPage = index;
                    pageImage.src = 'data:image/png;base64,' + imagesBase64[index];
                    pageInfo.textContent = 'Page ' + (index+1) + ' / ' + totalPages;
                    progressFill.style.width = ((index+1)/totalPages*100) + '%';
                    prevBtn.disabled = (index === 0);
                    nextBtn.disabled = (index === totalPages-1);

                    pageImage.style.opacity = '1';
                    pageImage.style.transform = 'scale(1)';
                    pageImage.classList.add('slide-transition');

                    if (index === totalPages - 1) {{
                        launchConfetti();
                    }}
                }}, 300);
            }}

            function launchConfetti() {{
                const colors = ['#ff69b4','#ff1493','#c2185b','#ffc0cb','#ffe6f0','#ffb6c1','#ff6b6b','#ffd93d'];
                for (let i = 0; i < 50; i++) {{
                    setTimeout(function() {{
                        var c = document.createElement('div');
                        c.className = 'confetti-piece';
                        c.style.left = Math.random() * 100 + 'vw';
                        c.style.background = colors[Math.floor(Math.random() * colors.length)];
                        c.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
                        c.style.width = (6 + Math.random() * 10) + 'px';
                        c.style.height = (6 + Math.random() * 10) + 'px';
                        c.style.animationDuration = (2 + Math.random() * 2) + 's';
                        c.style.animationDelay = (Math.random() * 0.5) + 's';
                        document.body.appendChild(c);
                        setTimeout(function() {{ c.remove(); }}, 4000);
                    }}, i * 70);
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
        st.progress((st.session_state
