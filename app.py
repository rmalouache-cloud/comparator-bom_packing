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

    /* Header logos animés */
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
    .logo-1 { animation: float  2.0s ease-in-out infinite; }
    .logo-2 { animation: bounce 2.2s ease-in-out infinite; }
    .logo-3 { animation: wiggle 1.8s ease-in-out infinite; }
    .logo-4 { animation: float  2.5s ease-in-out infinite 0.3s; }
    .logo-5 { animation: bounce 2.0s ease-in-out infinite 0.5s; }

    /* Titre animé */
    .main-title {
        text-align: center;
        animation: fadeInUp 0.8s ease-out;
    }
    .main-title h1 {
        background: linear-gradient(45deg, #ff69b4, #c2185b, #ff1493);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem !important;
        font-weight: 700;
        animation: none !important;
    }
    .subtitle {
        color: #c2185b;
        font-size: 18px;
        animation: pulse 3s ease-in-out infinite;
        display: inline-block;
    }

    /* Sidebar */
    .sidebar-avatar {
        font-size: 60px;
        text-align: center;
        animation: float 3s ease-in-out infinite;
        display: block;
    }
    .sidebar-title {
        text-align: center;
        background: linear-gradient(45deg, #ff69b4, #ff1493);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        font-size: 1.2rem;
        animation: rainbow 4s ease-in-out infinite;
        -webkit-text-fill-color: #ff69b4;
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

    /* Success banner */
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
</style>
""", unsafe_allow_html=True)

# ==============================
# BALLONS ANIMATION  (HTML + JS)
# ==============================
def show_balloons_animation():
    """Affiche des ballons qui volent vers le haut avec animation."""
    balloons_html = """
    <div class="balloons-container" id="balloonsContainer">
        <div class="balloon" style="left:5%;  animation-delay:0.0s; animation-duration:3.5s;">🎈</div>
        <div class="balloon" style="left:15%; animation-delay:0.2s; animation-duration:4.0s;">🎀</div>
        <div class="balloon" style="left:25%; animation-delay:0.1s; animation-duration:3.8s;">🎈</div>
        <div class="balloon" style="left:35%; animation-delay:0.3s; animation-duration:4.2s;">⭐</div>
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
        // Supprimer les ballons après 5 secondes
        setTimeout(function() {
            var container = document.getElementById('balloonsContainer');
            if (container) container.remove();
        }, 5000);
    </script>
    """
    st.markdown(balloons_html, unsafe_allow_html=True)
    st.balloons()  # Ballons natifs Streamlit en plus !

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
                transition: opacity 0.3s ease;
            }}
            .page-image.changing {{ opacity: 0; transform: scale(0.98); }}
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

            /* Confetti quand on finit toutes les pages */
            .confetti-piece {{
                position:fixed; width:10px; height:10px;
                top:-10px; opacity:0;
                animation: confettiFall 3s ease-in forwards;
            }}
            @keyframes confettiFall {{
                0%   {{ opacity:1; transform:translateY(0) rotate(0deg); }}
                100% {{ opacity:0; transform:translateY(100vh) rotate(720deg); }}
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
                <img id="pageImage" class="page-image"
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

                // Animation transition
                pageImage.style.opacity = '0';
                pageImage.style.transform = 'scale(0.97)';

                setTimeout(function() {{
                    currentPage = index;
                    pageImage.src = 'data:image/png;base64,' + imagesBase64[index];
                    pageInfo.textContent = 'Page ' + (index+1) + ' / ' + totalPages;
                    progressFill.style.width = ((index+1)/totalPages*100) + '%';
                    prevBtn.disabled = (index === 0);
                    nextBtn.disabled = (index === totalPages-1);

                    pageImage.style.opacity = '1';
                    pageImage.style.transform = 'scale(1)';

                    // Confetti à la dernière page
                    if (index === totalPages - 1) {{
                        launchConfetti();
                    }}
                }}, 200);
            }}

            function launchConfetti() {{
                const colors = ['#ff69b4','#ff1493','#c2185b','#ffc0cb','#ffe6f0','#ffb6c1'];
                for (let i = 0; i < 30; i++) {{
                    setTimeout(function() {{
                        var c = document.createElement('div');
                        c.className = 'confetti-piece';
                        c.style.left = Math.random() * 100 + 'vw';
                        c.style.background = colors[Math.floor(Math.random() * colors.length)];
                        c.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
                        c.style.animationDuration = (2 + Math.random() * 2) + 's';
                        c.style.animationDelay = (Math.random() * 0.5) + 's';
                        document.body.appendChild(c);
                        setTimeout(function() {{ c.remove(); }}, 4000);
                    }}, i * 80);
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

            // Transition image au chargement
            pageImage.style.transition = 'opacity 0.3s ease, transform 0.3s ease';

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

    # Header animé avec logos flottants
    st.markdown("""
        <div class="main-title">
            <h1>🌸 English Teacher's Platform 🌸</h1>
            <p><span class="subtitle">✨ Make learning beautiful and fun! ✨</span></p>
        </div>
        <div class="logo-container">
            <span class="logo-item logo-1">📖</span>
            <span class="logo-item logo-2">📝</span>
            <span class="logo-item logo-3">🎓</span>
            <span class="logo-item logo-4">✏️</span>
            <span class="logo-item logo-5">📕</span>
        </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
            <div style="padding:20px 0; text-align:center;">
                <span class="sidebar-avatar">👩‍🏫</span>
                <p class="sidebar-title">✨ Welcome! ✨</p>
            </div>
        """, unsafe_allow_html=True)
        mode = st.radio("Choose your role:",
                        ["👩‍🏫 Teacher", "👧 Student"], index=0)
        st.markdown("---")

        # Logos animés dans la sidebar
        st.markdown("""
            <div style="text-align:center; margin:10px 0;">
                <span style="font-size:25px; animation:float 2s ease-in-out infinite;
                             display:inline-block; margin:0 5px;">🌸</span>
                <span style="font-size:25px; animation:bounce 2.2s ease-in-out infinite;
                             display:inline-block; margin:0 5px;">⭐</span>
                <span style="font-size:25px; animation:wiggle 1.8s ease-in-out infinite;
                             display:inline-block; margin:0 5px;">💕</span>
            </div>
        """, unsafe_allow_html=True)
        st.caption("🌸 Made with love for English teachers 🌸")

    metadata = load_metadata()

    if st.session_state.viewing_course is not None:
        display_presentation(st.session_state.viewing_course)
    elif mode == "👩‍🏫 Teacher":
        teacher_mode(metadata)
    else:
        student_mode(metadata)

# ==============================
# TEACHER MODE
# ==============================
def teacher_mode(metadata):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
            <h3 style="animation:fadeInLeft 0.6s ease-out;">
                🌸 Upload New Course
            </h3>
        """, unsafe_allow_html=True)

        lc1, lc2 = st.columns(2)
        with lc1:
            level = st.selectbox("📚 Main Level", ["A", "B", "C"])
        with lc2:
            sub_level = st.selectbox("🎯 Sub-level", ["1", "2", "3"])
        full_level = f"{level}{sub_level}"

        title       = st.text_input("📖 Course Title",
                                    placeholder="e.g., Present Simple Tense")
        description = st.text_area("💭 Description",
                                   placeholder="What will students learn?")
        uploaded    = st.file_uploader("📎 Upload PDF File", type=["pdf"])

        if st.button("💖 Save Course", use_container_width=True):
            if title and uploaded:
                file_bytes   = uploaded.getbuffer().tobytes()
                storage_path = f"{full_level}/{uploaded.name}"
                course_id    = f"{full_level}_{uploaded.name}"

                with st.spinner("⬆️ Upload en cours… 🚀"):
                    upload_pdf(file_bytes, storage_path)
                    save_course(course_id, {
                        "title":        title,
                        "description":  description or "No description",
                        "level":        full_level,
                        "filename":     uploaded.name,
                        "storage_path": storage_path,
                        "upload_date":  time.strftime("%Y-%m-%d %H:%M"),
                    })

                # Animation ballons + message succès animé
                show_balloons_animation()
                st.markdown(f"""
                    <div class="success-banner">
                        🎉 Course "<strong>{title}</strong>" saved successfully! 🎉<br>
                        <span style="font-size:1.5rem;">🎈 🌸 ⭐ 💖 🎀</span>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(2)
                st.rerun()
            else:
                st.error("💔 Please add a title and file!")

    with col2:
        st.markdown("""
            <h3 style="animation:fadeInRight 0.6s ease-out;">📊 Quick Stats</h3>
        """, unsafe_allow_html=True)

        total = len(metadata)
        st.markdown(f"""
            <div class="stat-card">
                <div style="font-size:1rem; color:#888;">Total Courses</div>
                <div class="stat-number">📚 {total}</div>
            </div>
        """, unsafe_allow_html=True)

        if metadata:
            cnt = {}
            for c in metadata.values():
                cnt[c["level"]] = cnt.get(c["level"], 0) + 1
            st.write("")
            st.write("**📈 Courses per level:**")
            for lv, n in sorted(cnt.items()):
                st.progress(min(n / 10, 1.0), text=f"Level {lv}: {n} courses")

    st.markdown("---")
    st.markdown("""
        <h3 style="animation:fadeInUp 0.6s ease-out;">📚 Manage Your Courses</h3>
    """, unsafe_allow_html=True)

    if metadata:
        fl = st.selectbox("Filter by level:",
                          ["All"] + sorted({c["level"] for c in metadata.values()}))
        for key, course in metadata.items():
            if fl != "All" and course["level"] != fl:
                continue
            with st.container():
                ca, cb, cc = st.columns([3, 1, 1])
                with ca:
                    st.markdown(f"""
                        <div class="course-card fade-in">
                            <strong>📄 {course['title']}</strong><br>
                            <small>🎯 Level {course['level']}</small>&nbsp;
                            <small>📅 {course['upload_date']}</small><br>
                            <small>💭 {course['description']}</small>
                        </div>""", unsafe_allow_html=True)
                    if st.button("🎬 View & Present", key=f"view_{key}"):
                        for k in ['pdf_images', 'current_pdf_key', 'current_page']:
                            st.session_state.pop(k, None)
                        st.session_state.viewing_course = course
                        st.rerun()
                with cb:
                    pdf_bytes = download_pdf(course["storage_path"])
                    st.download_button("📥 Download", pdf_bytes,
                                       file_name=course["filename"],
                                       mime="application/pdf",
                                       key=f"down_{key}")
                with cc:
                    if st.button("🗑️ Delete", key=f"del_{key}"):
                        delete_pdf(course["storage_path"])
                        remove_course(key)
                        st.warning(f"💔 '{course['title']}' deleted")
                        time.sleep(0.5)
                        st.rerun()
    else:
        st.markdown("""
            <div style="text-align:center; padding:40px;" class="fade-in">
                <span class="bouncing" style="font-size:60px; display:inline-block;">📚</span>
                <p style="color:#c2185b; font-size:1.1rem; margin-top:15px;">
                    No courses yet. Upload your first course above!
                </p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# STUDENT MODE
# ==============================
def student_mode(metadata):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)

    st.markdown("""
        <h3 style="animation:fadeInUp 0.6s ease-out; text-align:center;">
            🎓 Browse Your Courses
        </h3>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        level = st.selectbox("📚 Select Main Level", ["A", "B", "C"])
    with c2:
        sub_level = st.selectbox("🎯 Select Sub-level", ["1", "2", "3"])

    full_level        = f"{level}{sub_level}"
    available_courses = {k: v for k, v in metadata.items()
                         if v["level"] == full_level}

    if available_courses:
        st.markdown(f"""
            <div style="text-align:center; margin:10px 0;" class="fade-in">
                <span style="background:linear-gradient(45deg,#ff69b4,#ff1493);
                             color:white; padding:10px 25px; border-radius:25px;
                             font-weight:bold; font-size:1rem;
                             box-shadow:0 4px 15px rgba(255,20,147,0.3);">
                    ✨ Found {len(available_courses)} course(s) for Level {full_level} ✨
                </span>
            </div>
        """, unsafe_allow_html=True)
        st.write("")

        for key, course in available_courses.items():
            with st.expander(f"📖 {course['title']}", expanded=True):
                ca, cb = st.columns([2, 1])
                with ca:
                    st.markdown(f"""
                        <div style="background:linear-gradient(135deg,#fff0f5,white);
                                    padding:15px; border-radius:15px;
                                    border:1px solid #ffc0cb;
                                    animation:fadeInLeft 0.6s ease-out;">
                            <strong>💭 Description:</strong><br>{course['description']}<br><br>
                            <strong>📅 Uploaded:</strong> {course['upload_date']}<br>
                            <strong>🎯 Level:</strong> {course['level']}<br>
                            <strong>📄 Type:</strong> PDF Document
                        </div>""", unsafe_allow_html=True)
                    if st.button("🎬 View Course", key=f"view_student_{key}"):
                        for k in ['pdf_images', 'current_pdf_key', 'current_page']:
                            st.session_state.pop(k, None)
                        st.session_state.viewing_course = course
                        st.rerun()
                with cb:
                    pdf_bytes = download_pdf(course["storage_path"])
                    st.download_button(
                        "📥 Download Course", pdf_bytes,
                        file_name=course["filename"],
                        mime="application/pdf",
                        use_container_width=True,
                        key=f"dl_s_{key}"
                    )
                if st.button("💡 Get a tip", key=f"tip_{key}"):
                    import random
                    tips = [
                        "✨ Take notes while reading!",
                        "💕 Practice with a friend!",
                        "⭐ Review key vocabulary after!",
                        "🌸 Ask questions if something is unclear!",
                        "🎯 Focus on one topic at a time!",
                        "📝 Write new words in a vocabulary notebook!"
                    ]
                    st.markdown(f"""
                        <div style="background:linear-gradient(135deg,#ffe6f0,#ffd9e8);
                                    padding:15px; border-radius:15px;
                                    border:2px solid #ffc0cb;
                                    animation:fadeInUp 0.4s ease-out;
                                    text-align:center; font-weight:bold; color:#c2185b;">
                            💖 {random.choice(tips)}
                        </div>
                    """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="text-align:center; padding:40px;" class="fade-in">
                <span class="floating" style="font-size:60px; display:inline-block;">📚</span>
                <br><br>
                <span class="bouncing" style="font-size:40px; display:inline-block;">✨</span>
                <p style="color:#c2185b; font-size:1.1rem; margin-top:15px;">
                    No courses available for Level {full_level} yet.<br>
                    Ask your teacher to upload courses!
                </p>
            </div>
        """.format(full_level=full_level), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    main()
