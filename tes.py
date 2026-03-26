import streamlit as st
import math
import pandas as pd

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Lifting Dashboard", layout="wide")

# =========================
# STYLE (BIAR KELIHATAN APP BANGET)
# =========================
st.markdown("""
<style>
.big-font {font-size:20px !important; font-weight:600;}
.safe {color: green; font-weight: bold;}
.danger {color: red; font-weight: bold;}
.warning {color: orange; font-weight: bold;}
.card {
    padding: 15px;
    border-radius: 10px;
    background-color: #f5f7fa;
}
</style>
""", unsafe_allow_html=True)

# =========================
# DATA OPTIONS
# =========================
SLING_OPTIONS = [1,2,3,5,8,10,13,17,20,25,32,40]
SHACKLE_OPTIONS = [1,2,3.25,4.75,6.5,8.5,9.5,12,17,25]
HOOK_OPTIONS = [5,10,15,20,30,50,100]

CRANE_CHART = {
    5:50,
    10:30,
    15:20,
    20:10,
    25:5
}

def get_crane_capacity(radius):
    for r in sorted(CRANE_CHART):
        if radius <= r:
            return CRANE_CHART[r]
    return 0

# =========================
# SIDEBAR INPUT
# =========================
st.sidebar.title("⚙️ Input Lifting")

load = st.sidebar.number_input("Load (ton)", 1.0, 200.0, 10.0)
legs = st.sidebar.selectbox("Number of Legs", [1,2,3,4])
angle = st.sidebar.slider("Angle (° from horizontal)", 0, 85, 60)
radius = st.sidebar.slider("Radius (m)", 5, 25, 15)

dynamic = st.sidebar.slider("Dynamic Factor", 1.0, 1.5, 1.1)
margin = st.sidebar.slider("Safety Margin", 1.0, 2.0, 1.25)
cog = st.sidebar.slider("COG Distribution", 0.3, 0.7, 0.5)

st.sidebar.markdown("---")

sling_type = st.sidebar.selectbox("Sling Type", ["Chain","Wire Rope","Webbing"])
sling = st.sidebar.selectbox("Sling Capacity (ton)", SLING_OPTIONS, index=4)
shackle = st.sidebar.selectbox("Shackle Capacity (ton)", SHACKLE_OPTIONS, index=4)
hook = st.sidebar.selectbox("Hook Capacity (ton)", HOOK_OPTIONS, index=2)

# =========================
# CALCULATION
# =========================
eff = 2 if legs==3 else 3 if legs==4 else legs

angle_v = 90 - angle
cos_a = math.cos(math.radians(angle_v))

worst = max(load*cog, load*(1-cog))

per_leg = worst/(eff*cos_a)
per_leg_dyn = per_leg * dynamic
total_dyn = load * dynamic

sling_req = per_leg_dyn
sling_rec = sling_req * margin

shackle_req = per_leg_dyn
shackle_rec = shackle_req * margin

hook_req = total_dyn
hook_rec = hook_req * margin

crane_req = total_dyn
crane_chart = get_crane_capacity(radius)

# =========================
# STATUS FUNCTION
# =========================
def status(actual, required):
    return "SAFE" if actual >= required else "NOT SAFE"

def risk_calc(ratio, angle, cog, sling_type):
    r = 0
    if angle > 60: r += 2
    if abs(cog-0.5)>0.1: r += 2
    if ratio > 0.8: r += 3
    if sling_type == "Webbing": r += 1

    if r <= 2: return "LOW"
    elif r <=5: return "MEDIUM"
    else: return "HIGH"

def color_status(val):
    if val == "SAFE":
        return "safe"
    else:
        return "danger"

# =========================
# DATAFRAME
# =========================
df = pd.DataFrame({
    "Equipment":["Sling","Shackle","Hook","Crane"],
    "Min Required":[sling_req, shackle_req, hook_req, crane_req],
    "Recommended":[sling_rec, shackle_rec, hook_rec, crane_req],
    "Actual":[sling, shackle, hook, crane_chart],
    "Utilization":[
        sling_req/sling,
        shackle_req/shackle,
        hook_req/hook,
        crane_req/crane_chart if crane_chart>0 else 1
    ],
    "Status":[
        status(sling, sling_rec),
        status(shackle, shackle_rec),
        status(hook, hook_rec),
        status(crane_chart, crane_req)
    ],
    "Risk":[
        risk_calc(sling_req/sling, angle, cog, sling_type),
        risk_calc(shackle_req/shackle, angle, cog, sling_type),
        risk_calc(hook_req/hook, angle, cog, sling_type),
        risk_calc(crane_req/crane_chart if crane_chart>0 else 1, angle, cog, sling_type)
    ]
}).round(2)

# =========================
# UI HEADER
# =========================
st.title("⚓ Offshore Lifting Dashboard")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Load (ton)", load)
col2.metric("Angle (°)", angle)
col3.metric("Legs", legs)
col4.metric("Radius (m)", radius)

st.markdown("---")

# =========================
# MAIN LAYOUT
# =========================
left, right = st.columns([2,1])

# ===== LEFT: TABLE =====
with left:
    st.subheader("📊 Equipment Calculation")

    st.dataframe(df, use_container_width=True)

# ===== RIGHT: SUMMARY =====
with right:
    st.subheader("📌 Summary")

    for i in range(len(df)):
        eq = df.loc[i,"Equipment"]
        stat = df.loc[i,"Status"]
        risk = df.loc[i,"Risk"]

        color = "green" if stat=="SAFE" else "red"

        st.markdown(f"""
        <div class="card">
        <b>{eq}</b><br>
        Status: <span style="color:{color}">{stat}</span><br>
        Risk: {risk}
        </div>
        """, unsafe_allow_html=True)

# =========================
# FINAL STATUS
# =========================
st.markdown("---")

if all(df["Status"]=="SAFE"):
    st.success("✅ FINAL STATUS: SAFE")
else:
    st.error("❌ FINAL STATUS: NOT SAFE")

# =========================
# WARNING
# =========================
if angle > 60:
    st.warning("⚠️ Angle > 60°, risk meningkat signifikan")

if abs(cog-0.5)>0.1:
    st.warning("⚠️ COG tidak simetris")
