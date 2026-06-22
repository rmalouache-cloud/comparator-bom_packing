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
import streamlit.components.v1 as components

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="✨ English Teacher's Platform ✨",
    page_icon="🌸",
    layout="wide"
)

# ==============================
# CUSTOM CSS + ANIMATIONS (Version corrigée !)
# ==============================
st.markdown("""
<style>
    /* Correction de l'application du dégradé d'arrière-plan sur Streamlit */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #ffe6f0 0%, #ffd9e8 50%, #ffe6f0 100%) !important;
        background-size: 400% 400% !important;
        animation: gradientShift 8s ease infinite !important;
    }
    
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* ===== TITRE SHIMMER QUI DÉFILE ===== */
    .shimmer-title {
        background: linear-gradient(90deg, #ff69b4, #c2185b, #ff1493, #ff69b4, #c2185b, #ff1493);
        background-size: 300% 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: shimmer 2s linear infinite !important;
        font-size: 2.8rem !important;
        font-weight: 700 !important;
        display: inline-block !important;
        padding: 10px !important;
        text-align: center !important;
        width: 100% !important;
    }

    @keyframes shimmer {
        0% { background-position: 0% 50%; }
        100% { background-position: 300% 50%; }
    }

    /* ===== LOGOS AVEC LEURS PROPRES ANIMATIONS ===== */
    .logo-container {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 30px !important;
        margin: 15px 0 25px 0 !important;
        flex-wrap: wrap !important;
        padding: 15px !important;
        background: rgba(255,255,255,0.3) !important;
        border-radius: 50px !important;
    }

    .logo-item {
        font-size: 50px !important;
        display: inline-block !important;
        padding: 5px !important;
        transition: transform 0.3s ease !important;
    }

    .logo-item:hover {
        transform: scale(1.5) rotate(15deg) !important;
    }

    /* 📖 flotter */
    .logo-float {
        animation: floatAnim 2.5s ease-in-out infinite !important;
    }
    /* 📝 rebondir */
    .logo-bounce {
        animation: bounceAnim 2s ease-in-out infinite !important;
    }
    /* 🎓 osciller */
    .logo-oscillate {
        animation: oscillateAnim 1.8s ease-in-out infinite !important;
    }
    /* ⭐ tourner */
    .logo-spin {
        animation: spinAnim 4s linear infinite !important;
    }
    /* 💖 battre comme un cœur */
    .logo-heartbeat {
        animation: heartbeatAnim 1.5s ease-in-out infinite !important;
    }

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

    /* ===== SIDEBAR AVATAR - Monte et descend ===== */
    .sidebar-avatar {
        font-size: 70px !important;
        text-align: center !important;
        animation: floatAnim 3s ease-in-out infinite !important;
        display: block !important;
        padding: 15px !important;
    }

    /* ===== SIDEBAR ICONS - Pulse en décalé ===== */
    .sidebar-icons {
        text-align: center !important;
        padding: 10px !important;
    }

    .sidebar-icon {
        font-size: 30px !important;
        display: inline-block !important;
        margin: 0 8px !important;
    }

    .icon-pulse-1 { 
        animation: pulseAnim 2s ease-in-out infinite !important; 
    }
    .icon-pulse-2 { 
        animation: pulseAnim 2.3s ease-in-out infinite 0.3s !important; 
    }
    .icon-pulse-3 { 
        animation: pulseAnim 2.6s ease-in-out infinite 0.6s !important; 
    }

    @keyframes pulseAnim {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.4); }
    }

    /* ===== SIDEBAR TITLE RAINBOW ===== */
    .sidebar-title {
        text-align: center !important;
        font-weight: 700 !important;
        font-size: 1.3rem !important;
        animation: rainbowAnim 3s linear infinite !important;
        padding: 10px !important;
    }

    @keyframes rainbowAnim {
        0% { color: #ff69b4; }
        25% { color: #ff1493; }
        50% { color: #c2185b; }
        75% { color: #ff69b4; }
        100% { color: #ff1493; }
    }

    /* ===== SUBTITLE PULSE ===== */
    .subtitle {
        color: #c2185b !important;
        font-size: 18px !important;
        animation: subtitlePulse 2s ease-in-out infinite !important;
        display: inline-block !important;
    }

    @keyframes subtitlePulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.7; transform: scale(1.05); }
    }

    /* ===== BOUTONS GLOW ===== */
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
        50% { box-shadow: 0 4px 35px rgba(255,20,147,0.7); }
    }

    .stButton > button:hover {
        transform: scale(1.08) translateY(-3px) !important;
    }

    /* ===== SUCCESS BANNER ===== */
    .success-banner {
        background: linear-gradient(135deg, #ff69b4, #ff1493) !important;
        color: white !important;
        border-radius: 20px !important;
        padding: 25px !important;
        text-align: center !important;
        font-size: 1.4rem !important;
        font-weight: bold !important;
        animation: bannerIn 0.5s ease-out, bannerPulse 2s ease-in-out infinite 0.5s !important;
        box-shadow: 0 10px 30px rgba(255,20,147,0.4) !important;
        margin: 15px 0 !important;
    }

    @keyframes bannerIn {
        from { opacity: 0; transform: scale(0.8) translateY(30px); }
        to { opacity: 1; transform: scale(1) translateY(0); }
    }

    @keyframes bannerPulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.03); }
    }

    /* ===== TRANSITIONS SLIDES - Fondu + mise à l'échelle ===== */
    .slide-transition {
        animation: slideFadeScale 0.6s ease-out !important;
    }

    @keyframes slideFadeScale {
        0% { opacity: 0; transform: scale(0.9); }
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

    /* Classes d'animation d'icônes */
    .floating { animation: floatAnim 3s ease-in-out infinite !important; }
    .pulsing { animation: pulseAnim 2s ease-in-out infinite !important; }
    .bouncing { animation: bounceAnim 1.5s ease-in-out infinite !important; }
    .heartbeat { animation: heartbeatAnim 1.5s ease-in-out infinite !important; }
    .spinning { animation: spinAnim 4s linear infinite !important; }
</style>
""", unsafe_allow_html=True)

# ==============================
# BALLONS ANIMATION (Corrigé !)
# ==============================
def show_balloons_animation():
    balloons_html = """
    <script>
        (function() {
            let doc = document;
            try {
                if (window.parent && window.parent.document) {
                    doc = window.parent.document;
                }
            } catch(e) {}

            var container = doc.createElement('div');
            container.id = 'balloonsContainer';
            container.style.position = 'fixed';
            container.style.bottom = '0';
            container.style.left = '0';
            container.style.width = '100vw';
            container.style.height = '100vh';
            container.style.pointerEvents = 'none';
            container.style.zIndex = '99999';
            container.style.overflow = 'hidden';

            // Injection dynamique des animations clés dans le contexte parent
            if (!doc.getElementById('balloon-styles')) {
                var style = doc.createElement('style');
                style.id = 'balloon-styles';
                style.innerHTML = `
                    @keyframes balloonFloat {
                        0% { transform: translateY(100vh) rotate(-5deg) scale(0.5); opacity: 1; }
                        100% { transform: translateY(-150px) rotate(5deg) scale(1); opacity: 0; }
                    }
                    @keyframes balloonSway {
                        0%, 100% { margin-left: 0px; }
                        25% { margin-left: 30px; }
                        75% { margin-left: -30px; }
                    }
                `;
                doc.head.appendChild(style);
            }

            const emojis = ['🎈', '🌸', '🎈', '💖', '🎈', '🌸', '🎈', '💖', '🎈', '✨', '🎊', '🎉', '💕'];
            for (let i = 0; i < 18; i++) {
                var b = doc.createElement('div');
                b.style.position = 'absolute';
                b.style.bottom = '-100px';
                b.style.fontSize = '55px';
                b.style.left = (Math.random() * 90 + 5) + '%';
                b.innerText = emojis[i % emojis.length];
                
                var duration = (3.5 + Math.random() * 1.5) + 's';
                var delay = (Math.random() * 0.6) + 's';
                b.style.animation = 'balloonFloat ' + duration + ' ease-out ' + delay + ' forwards, balloonSway 1.8s ease-in-out infinite';
                container.appendChild(b);
            }
            doc.body.appendChild(container);

            setTimeout(function() {
                container.remove();
            }, 6000);
        })();
    </script>
    """
    components.html(balloons_html, height=0, width=0)
    st.balloons()

# ==============================
# CONFETTI (Corrigé !)
# ==============================
def show_confetti():
    confetti_html = """
    <script>
        (function() {
            let doc = document;
            try {
                if (window.parent && window.parent.document) {
                    doc = window.parent.document;
                }
            } catch(e) {}

            const colors = ['#ff69b4','#ff1493','#c2185b','#ffc0cb','#ffe6f0','#ffb6c1','#ff6b6b','#ffd93d','#ff9ff3','#54a0ff'];
            
            if (!doc.getElementById('confetti-styles')) {
                var style = doc.createElement('style');
                style.id = 'confetti-styles';
                style.innerHTML = `
                    @keyframes confettiFall {
                        0% { opacity: 1; transform: translateY(0) rotate(0deg) scale(1); }
                        100% { opacity: 0; transform: translateY(110vh) rotate(720deg) scale(0.5); }
                    }
                `;
                doc.head.appendChild(style);
            }

            for (let i = 0; i < 60; i++) {
                setTimeout(function() {
                    var c = doc.createElement('div');
                    c.style.position = 'fixed';
                    c.style.width = (6 + Math.random() * 12) + 'px';
                    c.style.height = (6 + Math.random() * 12) + 'px';
                    c.style.left = Math.random() * 100 + 'vw';
                    c.style.top = '-10px';
                    c.style.zIndex = '100000';
                    c.style.pointerEvents = 'none';
                    c.style.opacity = '1';
                    c.style.background = colors[Math.floor(Math.random() * colors.length)];
                    c.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
                    
                    c.style.animation = 'confettiFall ' + (2 + Math.random() * 2.5) + 's ease-in forwards';
                    doc.body.appendChild(c);
                    
                    setTimeout(function() { c.remove(); }, 4000);
                }, i * 70);
            }
        })();
    </script>
    """
    components.html(confetti_html, height=0, width=0)

# ==============================
# HTML VIEWER (Transition slide corrigée avec déclencheur de reflow !)
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
                transition: opacity 0.3s ease, transform 0.3s ease;
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
                animation: slideFadeScale 0.5s ease-out !important;
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

                // On enlève temporairement l'animation
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
                    
                    // FORCE REFLOW : force le navigateur à recalculer avant de remettre la classe !
                    void pageImage.offsetWidth; 
                    pageImage.classList.add('slide-transition');

                    if (index === totalPages - 1) {{
                        launchConfetti();
                    }}
                }}, 150);
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
