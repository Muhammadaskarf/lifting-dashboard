import streamlit as st
import math
import pandas as pd

st.set_page_config(page_title="Lifting Dashboard", layout="wide")

# =========================
# STYLE
# =========================
st.markdown("""
<style>
.card {padding:15px;border-radius:12px;background:#f5f7fa;text-align:center;}
.card2 {padding:15px;border-radius:12px;background:#e3f2fd;text-align:center;}
.card-title {font-size:13px;color:#666;}
.card-value {font-size:20px;font-weight:bold;}
</style>
""", unsafe_allow_html=True)

# =========================
# OPTIONS
# =========================
SLING_OPTIONS = [1,2,3,5,8,10,13,17,20,25,32,40]
SHACKLE_OPTIONS = [1,2,3.25,4.75,6.5,8.5,9.5,12,17,25]
HOOK_OPTIONS = [5,10,15,20,30,50,100]

SLING_FACTOR = {
    "Chain": 1.0,
    "Wire Rope": 1.1,
    "Webbing": 1.25
}

CRANE_CHART_FACTOR = {
    5:1.0,
    10:0.8,
    15:0.6,
    20:0.4,
    25:0.25
}

def get_crane_factor(radius):
    for r in sorted(CRANE_CHART_FACTOR):
        if radius <= r:
            return CRANE_CHART_FACTOR[r]
    return 0.2

# =========================
# INPUT
# =========================
st.sidebar.title("⚙️ Input Lifting")

load = st.sidebar.number_input("Load (ton)", 1.0, 200.0, 10.0)
legs = st.sidebar.selectbox("Legs", [1,2,3,4])
angle = st.sidebar.slider("Angle (° from horizontal)", 0, 85, 60)
radius = st.sidebar.slider("Radius (m)", 5, 25, 15)

dynamic = st.sidebar.slider("Dynamic Factor", 1.0, 1.5, 1.1)
margin = st.sidebar.slider("Safety Margin", 1.0, 2.0, 1.25)
cog = st.sidebar.slider("COG Distribution", 0.3, 0.7, 0.5)

st.sidebar.markdown("---")

sling_type = st.sidebar.selectbox("Sling Type", ["Chain","Wire Rope","Webbing"])
sling = st.sidebar.selectbox("Sling Capacity (ton)", SLING_OPTIONS)
shackle = st.sidebar.selectbox("Shackle Capacity (ton)", SHACKLE_OPTIONS)
hook = st.sidebar.selectbox("Hook Capacity (ton)", HOOK_OPTIONS)
crane_input = st.sidebar.number_input("Crane Rated Capacity (ton)", 1.0, 500.0, 50.0)

# =========================
# CALCULATION
# =========================
eff = 2 if legs==3 else 3 if legs==4 else legs

angle_v = 90 - angle
cos_a = math.cos(math.radians(angle_v))

worst = max(load*cog, load*(1-cog))

# 🔥 PER LEG LOAD
per_leg = worst/(eff*cos_a)

# 🔥 APPLY DYNAMIC
per_leg_dyn = per_leg * dynamic
total_dyn = load * dynamic

# =========================
# EQUIPMENT LOGIC
# =========================
sling_factor = SLING_FACTOR[sling_type]

# Sling
sling_req = per_leg_dyn * sling_factor
sling_rec = sling_req * margin

# Shackle
shackle_req = per_leg_dyn
shackle_rec = shackle_req * margin

# Hook
hook_req = total_dyn
hook_rec = hook_req * margin

# Crane
crane_factor = get_crane_factor(radius)
crane_available = crane_input * crane_factor

crane_req = total_dyn
crane_rec = crane_req * margin

# =========================
# STATUS
# =========================
def status(actual, required):
    return "SAFE" if actual >= required else "NOT SAFE"

df = pd.DataFrame({
    "Equipment":["Sling","Shackle","Hook","Crane"],
    "Min Required":[sling_req, shackle_req, hook_req, crane_req],
    "Recommended":[sling_rec, shackle_rec, hook_rec, crane_rec],
    "Actual":[sling, shackle, hook, crane_available],
    "Utilization":[
        sling_req/sling,
        shackle_req/shackle,
        hook_req/hook,
        crane_req/crane_available if crane_available>0 else 1
    ],
    "Status":[
        status(sling, sling_rec),
        status(shackle, shackle_rec),
        status(hook, hook_rec),
        status(crane_available, crane_rec)
    ]
})

# =========================
# UI
# =========================
st.title("⚓ Offshore Lifting Dashboard")

# Row 1
r1 = st.columns(4)
r1[0].markdown(f'<div class="card">Load<br>{load:.2f} ton</div>', unsafe_allow_html=True)
r1[1].markdown(f'<div class="card">Angle<br>{angle:.2f}°</div>', unsafe_allow_html=True)
r1[2].markdown(f'<div class="card">Legs<br>{legs}</div>', unsafe_allow_html=True)
r1[3].markdown(f'<div class="card">Radius<br>{radius:.2f} m</div>', unsafe_allow_html=True)

# Row 2
r2 = st.columns(4)
r2[0].markdown(f'<div class="card2">Sling ({sling_type})<br>{sling:.2f} ton</div>', unsafe_allow_html=True)
r2[1].markdown(f'<div class="card2">Shackle<br>{shackle:.2f} ton</div>', unsafe_allow_html=True)
r2[2].markdown(f'<div class="card2">Hook<br>{hook:.2f} ton</div>', unsafe_allow_html=True)
r2[3].markdown(f'<div class="card2">Crane<br>{crane_input:.2f} ton<br><small>Available: {crane_available:.2f}</small></div>', unsafe_allow_html=True)

st.markdown("---")

st.dataframe(df.style.format("{:.2f}"), use_container_width=True)

if all(df["Status"]=="SAFE"):
    st.success("✅ SAFE")
else:
    st.error("❌ NOT SAFE")
