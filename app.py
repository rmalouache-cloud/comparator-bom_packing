import streamlit as st
import json
import os
import time
import io
import base64
import fitz  # PyMuPDF
from PIL import Image
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
# CSS MINIMAL  (juste ce que Streamlit accepte vraiment)
# ==============================
st.markdown("""
<style>
    .stApp { background: #ffeef6; }

    .stButton > button {
        background: linear-gradient(45deg, #ff69b4, #ff1493) !important;
        color: white !important;
        border-radius: 25px !important;
        border: none !important;
        padding: 12px 25px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(255,20,147,0.35) !important;
    }
    .stButton > button:hover {
        box-shadow: 0 8px 25px rgba(255,20,147,0.55) !important;
        transform: translateY(-2px) !important;
    }
    .course-card {
        background: white;
        border-radius: 18px;
        padding: 18px;
        margin: 8px 0;
        box-shadow: 0 4px 14px rgba(0,0,0,0.07);
        border: 1.5px solid #ffc0cb;
        transition: box-shadow .3s, transform .3s;
    }
    .course-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 30px rgba(255,20,147,.18);
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# ANIMATED HEADER  (tout dans une iframe propre)
# ==============================
HEADER_HTML = """
<!DOCTYPE html><html><head>
<meta charset="UTF-8">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family: 'Segoe UI', Arial, sans-serif;
  background: linear-gradient(135deg,#ffe6f0,#ffd9e8,#ffe6f0);
  background-size: 300% 300%;
  animation: bg 8s ease infinite;
  padding: 16px 10px 8px;
  overflow: hidden;
}
@keyframes bg {
  0%  { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100%{ background-position: 0% 50%; }
}
@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position:  200% center; }
}
@keyframes fadeDown {
  from { opacity:0; transform:translateY(-30px); }
  to   { opacity:1; transform:translateY(0); }
}
@keyframes pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.06)} }
@keyframes float {
  0%,100%{ transform:translateY(0) rotate(0deg); }
  33%    { transform:translateY(-16px) rotate(-6deg); }
  66%    { transform:translateY(-7px)  rotate(6deg); }
}
@keyframes bounce {
  0%,100%{ transform:translateY(0)   scale(1);   }
  40%    { transform:translateY(-20px) scale(1.12); }
  70%    { transform:translateY(-9px)  scale(1.05); }
}
@keyframes wiggle {
  0%,100%{ transform:rotate(0)   scale(1);   }
  25%    { transform:rotate(-16deg) scale(1.12); }
  75%    { transform:rotate(16deg)  scale(1.12); }
}
@keyframes spin {
  0%   { transform:rotate(0deg)   scale(1);   }
  50%  { transform:rotate(180deg) scale(1.2); }
  100% { transform:rotate(360deg) scale(1);   }
}
@keyframes heartbeat {
  0%,100%{ transform:scale(1);   }
  14%    { transform:scale(1.3); }
  28%    { transform:scale(1);   }
  42%    { transform:scale(1.2); }
  70%    { transform:scale(1);   }
}

/* Title */
.title {
  text-align:center;
  animation: fadeDown .8s ease-out;
}
.title-text {
  font-size: 2.2rem; font-weight:800;
  background: linear-gradient(90deg,#ff69b4 0%,#ff1493 25%,#c2185b 50%,#ff69b4 75%,#ff1493 100%);
  background-size: 200% auto;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shimmer 3s linear infinite;
  display: inline-block;
}
.subtitle {
  color:#c2185b; font-size:1rem; margin-top:4px;
  animation: pulse 2.5s ease-in-out infinite;
  display:inline-block;
}

/* Logos */
.logos { display:flex; justify-content:center; gap:20px; margin:14px 0 6px; flex-wrap:wrap; }
.logo {
  font-size:46px; display:inline-block; cursor:default;
  filter: drop-shadow(0 3px 6px rgba(255,20,147,.3));
  transition: transform .2s;
}
.logo:hover { transform: scale(1.5) !important; }
.l1 { animation: float     2.4s ease-in-out infinite 0.0s; }
.l2 { animation: bounce    2.0s ease-in-out infinite 0.2s; }
.l3 { animation: wiggle    1.8s ease-in-out infinite 0.1s; }
.l4 { animation: spin      5.0s ease-in-out infinite 0.3s; }
.l5 { animation: heartbeat 1.6s ease-in-out infinite 0.2s; }
.l6 { animation: float     3.0s ease-in-out infinite 0.4s; }
.l7 { animation: bounce    2.6s ease-in-out infinite 0.1s; }
</style></head><body>
<div class="title">
  <div class="title-text">🌸 English Teacher's Platform 🌸</div><br>
  <span class="subtitle">✨ Make learning beautiful and fun! ✨</span>
</div>
<div class="logos">
  <span class="logo l1">📖</span>
  <span class="logo l2">📝</span>
  <span class="logo l3">🎓</span>
  <span class="logo l4">⭐</span>
  <span class="logo l5">💖</span>
  <span class="logo l6">📕</span>
  <span class="logo l7">✏️</span>
</div>
</body></html>
"""

# ── Ballons HTML (appelé après Save) ──────────────────────────────────────
BALLOONS_HTML = """
<!DOCTYPE html><html><head>
<meta charset="UTF-8">
<style>
* { margin:0; padding:0; }
body { background:transparent; overflow:hidden; height:320px; position:relative; }
@keyframes rise {
  0%   { bottom:-80px; opacity:1; }
  80%  { opacity:1; }
  100% { bottom:120%; opacity:0; }
}
@keyframes sway {
  0%,100%{ transform:rotate(-10deg); }
  50%    { transform:rotate(10deg); }
}
.b {
  position:absolute;
  font-size:54px;
  animation: rise 4s ease-out forwards, sway 1.1s ease-in-out infinite;
  transform-origin: bottom center;
}
.success {
  position:absolute; top:50%; left:50%;
  transform: translate(-50%,-50%);
  background: linear-gradient(135deg,#ff69b4,#ff1493);
  color:white; border-radius:20px; padding:20px 30px;
  font-size:1.3rem; font-weight:bold; text-align:center;
  box-shadow: 0 10px 30px rgba(255,20,147,.5);
  animation: popIn .4s cubic-bezier(.175,.885,.32,1.275) both;
  white-space: nowrap;
  z-index:10;
}
@keyframes popIn {
  from { transform:translate(-50%,-50%) scale(0); opacity:0; }
  to   { transform:translate(-50%,-50%) scale(1); opacity:1; }
}
</style></head><body>
<div class="success" id="msg">🎉 Course saved! 🎈</div>
<div id="wrap"></div>
<script>
var EMOJI = ['🎈','🎀','🌸','⭐','💖','🎊','🎉','💕','✨'];
var wrap  = document.getElementById('wrap');
var msg   = document.getElementById('msg');

// Inject course title from URL param
var params = new URLSearchParams(window.location.search);
var title  = params.get('title') || 'Course';
msg.innerHTML = '🎉 &ldquo;' + title + '&rdquo; saved! 🎈<br><span style="font-size:1.6rem">🌸 ⭐ 💖 🎀 ✨</span>';

for (var i = 0; i < 16; i++) {
  (function(idx) {
    setTimeout(function() {
      var b = document.createElement('span');
      b.className = 'b';
      b.textContent = EMOJI[Math.floor(Math.random() * EMOJI.length)];
      b.style.left = (2 + Math.random() * 92) + '%';
      var dur1 = (3.0 + Math.random() * 2.0).toFixed(1);
      var dur2 = (0.8 + Math.random() * 0.7).toFixed(1);
      b.style.animationDuration = dur1 + 's, ' + dur2 + 's';
      wrap.appendChild(b);
      setTimeout(function() { b.remove(); }, 6500);
    }, idx * 140);
  })(i);
}
</script>
</body></html>
"""

# ==============================
# SIDEBAR HTML (avatar animé)
# ==============================
def sidebar_html(mode):
    return f"""
<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:transparent; font-family:'Segoe UI',Arial,sans-serif; padding:10px; }}
@keyframes float {{
  0%,100%{{ transform:translateY(0); }}
  50%    {{ transform:translateY(-12px); }}
}}
@keyframes pulse {{ 0%,100%{{transform:scale(1)}} 50%{{transform:scale(1.08)}} }}
@keyframes shimmer {{
  0%   {{ background-position:-200% center; }}
  100% {{ background-position: 200% center; }}
}}
.avatar {{ font-size:62px; text-align:center; display:block; animation:float 3s ease-in-out infinite; }}
.name {{
  text-align:center; font-size:1.1rem; font-weight:700; margin-top:6px;
  background:linear-gradient(90deg,#ff69b4,#ff1493,#c2185b,#ff69b4);
  background-size:200% auto;
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  background-clip:text;
  animation: shimmer 3s linear infinite;
}}
.icons {{ display:flex; justify-content:center; gap:10px; margin-top:10px; }}
.ic {{ font-size:22px; animation:pulse 2s ease-in-out infinite; }}
.ic:nth-child(2){{ animation-delay:.3s; }}
.ic:nth-child(3){{ animation-delay:.6s; }}
</style></head><body>
<span class="avatar">{"👩‍🏫" if "Teacher" in mode else "👧"}</span>
<div class="name">✨ Welcome! ✨</div>
<div class="icons"><span class="ic">🌸</span><span class="ic">⭐</span><span class="ic">💕</span></div>
</body></html>
"""

# ==============================
# SUPABASE
# ==============================
BUCKET = "courses"

@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def load_metadata() -> dict:
    try:
        rows = get_supabase().table("courses").select("*").execute().data
        return {r["id"]: r for r in rows}
    except Exception as e:
        st.error(f"❌ Cannot load courses: {e}")
        return {}

def save_course(course_id, data):
    get_supabase().table("courses").upsert({"id": course_id, **data}).execute()

def remove_course(course_id):
    get_supabase().table("courses").delete().eq("id", course_id).execute()

def upload_pdf(file_bytes, storage_path):
    get_supabase().storage.from_(BUCKET).upload(
        storage_path, file_bytes,
        {"content-type": "application/pdf", "upsert": "true"}
    )

def download_pdf(storage_path):
    return get_supabase().storage.from_(BUCKET).download(storage_path)

def delete_pdf(storage_path):
    get_supabase().storage.from_(BUCKET).remove([storage_path])

# ==============================
# PDF → BASE64 IMAGES
# ==============================
def pdf_bytes_to_b64(pdf_bytes):
    doc  = fitz.open(stream=pdf_bytes, filetype="pdf")
    imgs = []
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        if img.width > 1200:
            img = img.resize((1200, int(img.height * 1200 / img.width)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "PNG", optimize=True)
        imgs.append(base64.b64encode(buf.getvalue()).decode())
    doc.close()
    return imgs

# ==============================
# HTML VIEWER (fullscreen + transitions)
# ==============================
def create_html_viewer(images_b64, title):
    total = len(images_b64)
    imgs_js = "[\n" + ",\n".join(f'  "data:image/png;base64,{b}"' for b in images_b64) + "\n]"
    return f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',Arial,sans-serif;
     background:linear-gradient(135deg,#ffe6f0,#ffd9e8);padding:16px;}}
.box{{max-width:1080px;margin:0 auto;background:white;border-radius:20px;
      padding:24px;box-shadow:0 10px 30px rgba(0,0,0,.1);
      animation:fadeUp .5s ease-out;}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(20px)}}to{{opacity:1;transform:translateY(0)}}}}
.box:fullscreen,.box:-webkit-full-screen,.box:-moz-full-screen{{
  max-width:100%;width:100vw;height:100vh;border-radius:0;
  display:flex;flex-direction:column;justify-content:center;overflow-y:auto;}}
.top{{display:flex;justify-content:space-between;align-items:center;
      margin-bottom:12px;flex-wrap:wrap;gap:8px;}}
.ttl{{font-size:1.2rem;font-weight:700;
      background:linear-gradient(90deg,#ff69b4,#c2185b);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}
.badge{{background:#ffe6f0;color:#c2185b;font-weight:700;
        padding:6px 16px;border-radius:20px;border:2px solid #ffc0cb;font-size:.95rem;}}
.prog{{width:100%;height:8px;background:#f0f0f0;border-radius:4px;
       overflow:hidden;margin:8px 0 16px;}}
.prog-fill{{height:100%;background:linear-gradient(90deg,#ff69b4,#ff1493);
            border-radius:4px;transition:width .4s ease;}}
.img-wrap{{display:flex;justify-content:center;align-items:center;
           min-height:380px;background:#fafafa;border-radius:12px;
           padding:8px;margin-bottom:16px;}}
#slide{{max-width:100%;max-height:68vh;border-radius:8px;
        box-shadow:0 4px 14px rgba(0,0,0,.1);
        transition:opacity .3s ease,transform .3s ease;}}
.nav{{display:flex;justify-content:center;gap:14px;flex-wrap:wrap;}}
button{{background:linear-gradient(45deg,#ff69b4,#ff1493);color:white;
        border:none;border-radius:25px;padding:11px 28px;font-weight:700;
        font-size:.95rem;cursor:pointer;min-width:130px;
        box-shadow:0 4px 14px rgba(255,20,147,.35);
        transition:transform .2s,box-shadow .2s;}}
button:hover:not(:disabled){{transform:translateY(-3px) scale(1.06);
  box-shadow:0 8px 24px rgba(255,20,147,.5);}}
button:active:not(:disabled){{transform:scale(.97);}}
button:disabled{{opacity:.4;cursor:not-allowed;transform:none;}}
#fsBtn{{background:linear-gradient(45deg,#7c3aed,#5b21b6);}}
@keyframes confFall{{
  0%  {{opacity:1;transform:translateY(0) rotate(0deg);}}
  100%{{opacity:0;transform:translateY(100vh) rotate(720deg);}}
}}
</style></head><body>
<div class="box" id="box">
  <div class="top">
    <div class="ttl">📖 {title}</div>
    <div style="display:flex;gap:8px;align-items:center;">
      <div class="badge" id="badge">1 / {total}</div>
      <button id="fsBtn" onclick="toggleFS()">⛶ Plein écran</button>
    </div>
  </div>
  <div class="prog"><div class="prog-fill" id="pf" style="width:{100/total:.1f}%"></div></div>
  <div class="img-wrap"><img id="slide" src="" alt="slide"/></div>
  <div class="nav">
    <button id="bFirst" onclick="go(0)">⏮ Premier</button>
    <button id="bPrev"  onclick="go(cur-1)">◀ Précédent</button>
    <button id="bNext"  onclick="go(cur+1)">Suivant ▶</button>
    <button id="bLast"  onclick="go(tot-1)">Dernier ⏭</button>
  </div>
</div>
<script>
const imgs={imgs_js};
const tot={total};
let cur=0;
const slide=document.getElementById('slide');
const badge=document.getElementById('badge');
const pf   =document.getElementById('pf');
const bPrev=document.getElementById('bPrev');
const bNext=document.getElementById('bNext');
const bFirst=document.getElementById('bFirst');
const bLast=document.getElementById('bLast');

function go(n){{
  n=Math.max(0,Math.min(tot-1,n));
  slide.style.opacity='0'; slide.style.transform='scale(.97)';
  setTimeout(function(){{
    cur=n;
    slide.src=imgs[n];
    badge.textContent=(n+1)+' / '+tot;
    pf.style.width=((n+1)/tot*100)+'%';
    bPrev.disabled=bFirst.disabled=(n===0);
    bNext.disabled=bLast.disabled=(n===tot-1);
    slide.style.opacity='1'; slide.style.transform='scale(1)';
    if(n===tot-1) confetti();
  }},220);
}}
function confetti(){{
  var cols=['#ff69b4','#ff1493','#c2185b','#ffc0cb','#ffb6c1'];
  for(var i=0;i<35;i++){{
    (function(i){{setTimeout(function(){{
      var d=document.createElement('div');
      d.style.cssText='position:fixed;width:10px;height:10px;top:-10px;z-index:9999;'+
        'left:'+(Math.random()*100)+'vw;'+
        'background:'+cols[Math.floor(Math.random()*cols.length)]+';'+
        'border-radius:'+(Math.random()>.5?'50%':'0')+';'+
        'animation:confFall '+(2+Math.random()*2)+'s ease-in forwards;'+
        'animation-delay:'+(Math.random()*.4)+'s;';
      document.body.appendChild(d);
      setTimeout(function(){{d.remove();}},4500);
    }},i*70);}}})(i);
  }}
}}
function toggleFS(){{
  var el=document.getElementById('box');
  var fs=document.fullscreenElement||document.webkitFullscreenElement||document.mozFullScreenElement;
  if(!fs)(el.requestFullscreen||el.webkitRequestFullscreen||el.mozRequestFullScreen).call(el);
  else (document.exitFullscreen||document.webkitExitFullscreen||document.mozCancelFullScreen).call(document);
}}
document.addEventListener('keydown',function(e){{
  if(e.key==='ArrowRight'||e.key==='ArrowDown') go(cur+1);
  if(e.key==='ArrowLeft' ||e.key==='ArrowUp')   go(cur-1);
  if(e.key==='Home') go(0); if(e.key==='End') go(tot-1);
  if(e.key==='f'||e.key==='F') toggleFS();
}});
slide.style.transition='opacity .3s ease,transform .3s ease';
go(0);
</script></body></html>"""

# ==============================
# DISPLAY PRESENTATION
# ==============================
def display_presentation(course):
    if st.button("◀ Retour aux cours"):
        st.session_state.viewing_course = None
        for k in ['pdf_images','current_pdf_key']:
            st.session_state.pop(k, None)
        st.rerun()

    course_key = course["id"]
    if st.session_state.get('current_pdf_key') != course_key:
        with st.spinner("🔄 Chargement du cours…"):
            try:
                pdf_bytes = download_pdf(course["storage_path"])
                imgs      = pdf_bytes_to_b64(pdf_bytes)
                st.session_state.pdf_images      = imgs
                st.session_state.current_pdf_key = course_key
            except Exception as e:
                st.error(f"❌ Erreur : {e}"); return

    imgs = st.session_state.get("pdf_images", [])
    if not imgs:
        st.warning("Aucune page trouvée."); return

    st.components.v1.html(
        create_html_viewer(imgs, course["title"]),
        height=760, scrolling=False
    )
    st.caption("💡 Touches ← → pour naviguer · F ou ⛶ pour plein écran")
    st.markdown("---")
    with st.expander("📥 Télécharger le PDF"):
        pdf = download_pdf(course["storage_path"])
        st.download_button("Télécharger", pdf,
                           file_name=course["filename"], mime="application/pdf")

# ==============================
# MAIN
# ==============================
def main():
    if 'viewing_course' not in st.session_state:
        st.session_state.viewing_course = None
    if 'show_balloons' not in st.session_state:
        st.session_state.show_balloons = False
    if 'saved_title' not in st.session_state:
        st.session_state.saved_title = ""

    # ── Header animé complet ──
    st.components.v1.html(HEADER_HTML, height=230, scrolling=False)

    # ── Ballons si just saved ──
    if st.session_state.show_balloons:
        title_enc = st.session_state.saved_title.replace('"','').replace("'","")
        balloon_html = BALLOONS_HTML.replace(
            "var title  = params.get('title') || 'Course';",
            f"var title = '{title_enc}';"
        )
        st.components.v1.html(balloon_html, height=320, scrolling=False)
        st.session_state.show_balloons = False

    with st.sidebar:
        mode = st.radio("Choose your role:",
                        ["👩‍🏫 Teacher", "👧 Student"], index=0)
        st.components.v1.html(sidebar_html(mode), height=130, scrolling=False)
        st.markdown("---")
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
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🌸 Upload New Course")
        lc1, lc2 = st.columns(2)
        with lc1: level     = st.selectbox("📚 Main Level", ["A","B","C"])
        with lc2: sub_level = st.selectbox("🎯 Sub-level", ["1","2","3"])
        full_level  = f"{level}{sub_level}"
        title       = st.text_input("📖 Course Title", placeholder="e.g., Present Simple Tense")
        description = st.text_area("💭 Description",  placeholder="What will students learn?")
        uploaded    = st.file_uploader("📎 Upload PDF File", type=["pdf"])

        if st.button("💖 Save Course", use_container_width=True):
            if title and uploaded:
                fb = uploaded.getbuffer().tobytes()
                sp = f"{full_level}/{uploaded.name}"
                cid = f"{full_level}_{uploaded.name}"
                with st.spinner("⬆️ Uploading… 🚀"):
                    upload_pdf(fb, sp)
                    save_course(cid, {
                        "title": title, "description": description or "No description",
                        "level": full_level, "filename": uploaded.name,
                        "storage_path": sp,
                        "upload_date": time.strftime("%Y-%m-%d %H:%M"),
                    })
                st.session_state.show_balloons = True
                st.session_state.saved_title   = title
                st.rerun()
            else:
                st.error("💔 Please add a title and file!")

    with col2:
        st.subheader("📊 Quick Stats")
        st.markdown(f"""
        <div style="background:white;border-radius:16px;padding:18px;text-align:center;
                    border:2px solid #ffc0cb;box-shadow:0 4px 14px rgba(255,20,147,.12);">
          <div style="color:#888;font-size:.9rem;">Total Courses</div>
          <div style="font-size:2.4rem;font-weight:800;color:#ff1493;">📚 {len(metadata)}</div>
        </div>""", unsafe_allow_html=True)
        if metadata:
            cnt = {}
            for c in metadata.values(): cnt[c["level"]] = cnt.get(c["level"],0)+1
            st.write("")
            for lv,n in sorted(cnt.items()):
                st.progress(min(n/10,1.0), text=f"Level {lv}: {n} course(s)")

    st.markdown("---")
    st.subheader("📚 Manage Your Courses")

    if metadata:
        fl = st.selectbox("Filter:", ["All"]+sorted({c["level"] for c in metadata.values()}))
        for key, course in metadata.items():
            if fl != "All" and course["level"] != fl: continue
            ca, cb, cc = st.columns([3,1,1])
            with ca:
                st.markdown(f"""
                <div class="course-card">
                  <strong>📄 {course['title']}</strong><br>
                  <small>🎯 Level {course['level']} &nbsp;|&nbsp; 📅 {course['upload_date']}</small><br>
                  <small>💭 {course['description']}</small>
                </div>""", unsafe_allow_html=True)
                if st.button("🎬 View & Present", key=f"v_{key}"):
                    for k in ['pdf_images','current_pdf_key']:
                        st.session_state.pop(k, None)
                    st.session_state.viewing_course = course
                    st.rerun()
            with cb:
                pdf = download_pdf(course["storage_path"])
                st.download_button("📥 Download", pdf,
                                   file_name=course["filename"],
                                   mime="application/pdf", key=f"d_{key}")
            with cc:
                if st.button("🗑️ Delete", key=f"del_{key}"):
                    delete_pdf(course["storage_path"]); remove_course(key)
                    st.warning(f"💔 '{course['title']}' deleted")
                    time.sleep(.5); st.rerun()
    else:
        st.info("🌸 No courses yet. Upload your first course above!")

# ==============================
# STUDENT MODE
# ==============================
def student_mode(metadata):
    st.subheader("🎓 Browse Your Courses")
    c1,c2 = st.columns(2)
    with c1: level     = st.selectbox("📚 Select Main Level", ["A","B","C"])
    with c2: sub_level = st.selectbox("🎯 Select Sub-level",  ["1","2","3"])
    full_level = f"{level}{sub_level}"
    avail = {k:v for k,v in metadata.items() if v["level"]==full_level}

    if avail:
        st.success(f"✨ Found {len(avail)} course(s) for Level {full_level} ✨")
        for key, course in avail.items():
            with st.expander(f"📖 {course['title']}", expanded=True):
                ca,cb = st.columns([2,1])
                with ca:
                    st.markdown(f"""
                    <div style="background:#fff0f5;padding:15px;border-radius:15px;
                                border:1px solid #ffc0cb;">
                      <strong>💭 Description:</strong><br>{course['description']}<br><br>
                      <strong>📅 Uploaded:</strong> {course['upload_date']}<br>
                      <strong>🎯 Level:</strong> {course['level']}
                    </div>""", unsafe_allow_html=True)
                    if st.button("🎬 View Course", key=f"vs_{key}"):
                        for k in ['pdf_images','current_pdf_key']:
                            st.session_state.pop(k,None)
                        st.session_state.viewing_course = course
                        st.rerun()
                with cb:
                    pdf = download_pdf(course["storage_path"])
                    st.download_button("📥 Download", pdf,
                                       file_name=course["filename"],
                                       mime="application/pdf",
                                       use_container_width=True,
                                       key=f"ds_{key}")
                if st.button("💡 Get a tip", key=f"t_{key}"):
                    import random
                    tips=["✨ Take notes while reading!","💕 Practice with a friend!",
                          "⭐ Review key vocabulary after!","🌸 Ask questions!",
                          "🎯 Focus on one topic at a time!","📝 Write new words in a notebook!"]
                    st.info(f"💖 {random.choice(tips)}")
    else:
        st.warning(f"💔 No courses available for Level {full_level} yet.")

if __name__ == "__main__":
    main()
