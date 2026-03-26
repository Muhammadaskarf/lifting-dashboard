import streamlit as st
import math
import pandas as pd

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Lifting Dashboard", layout="wide")

# =========================
# STYLE
# =========================
st.markdown("""
<style>
.card {
    padding: 15px;
    border-radius: 12px;
    background-color: #f5f7fa;
    text-align: center;
}
.card2 {
    padding: 15px;
    border-radius: 12px;
    background-color: #e3f2fd;
    text-align: center;
}
.card-title {
    font-size: 13px;
    color: #666;
}
.card-value {
    font-size: 20px;
    font-weight: bold;
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
# INPUT
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
crane_input = st.sidebar.number_input("Crane Capacity Actual (ton)", 1.0, 500.0, 20.0)

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
# STATUS & RISK
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

# =========================
# DATAFRAME
# =========================
df = pd.DataFrame({
    "Equipment":["Sling","Shackle","Hook","Crane"],
    "Min Required":[sling_req, shackle_req, hook_req, crane_req],
    "Recommended":[sling_rec, shackle_rec, hook_rec, crane_req],
    "Actual":[sling, shackle, hook, crane_input],
    "Utilization":[
        sling_req/sling,
        shackle_req/shackle,
        hook_req/hook,
        crane_req/crane_input if crane_input>0 else 1
    ],
    "Status":[
        status(sling, sling_rec),
        status(shackle, shackle_rec),
        status(hook, hook_rec),
        status(crane_input, crane_req)
    ],
    "Risk":[
        risk_calc(sling_req/sling, angle, cog, sling_type),
        risk_calc(shackle_req/shackle, angle, cog, sling_type),
        risk_calc(hook_req/hook, angle, cog, sling_type),
        risk_calc(crane_req/crane_input if crane_input>0 else 1, angle, cog, sling_type)
    ]
})

# =========================
# STYLE TABLE
# =========================
def highlight(val):
    if val == "SAFE":
        return "color: green; font-weight:bold"
    if val == "NOT SAFE":
        return "color: red; font-weight:bold"
    if val == "LOW":
        return "color: green; font-weight:bold"
    if val == "MEDIUM":
        return "color: orange; font-weight:bold"
    if val == "HIGH":
        return "color: red; font-weight:bold"
    return ""

styled_df = df.style.format({
    "Min Required": "{:.2f}",
    "Recommended": "{:.2f}",
    "Actual": "{:.2f}",
    "Utilization": "{:.2f}"
}).applymap(highlight)

# =========================
# UI
# =========================
st.title("⚓ Offshore Lifting Dashboard")

# 🔹 ROW 1 - LIFTING PARAMETER
row1 = st.columns(4)

row1[0].markdown(f'<div class="card"><div class="card-title">Load</div><div class="card-value">{load:.2f} ton</div></div>', unsafe_allow_html=True)
row1[1].markdown(f'<div class="card"><div class="card-title">Angle</div><div class="card-value">{angle:.2f} °</div></div>', unsafe_allow_html=True)
row1[2].markdown(f'<div class="card"><div class="card-title">Legs</div><div class="card-value">{legs}</div></div>', unsafe_allow_html=True)
row1[3].markdown(f'<div class="card"><div class="card-title">Radius</div><div class="card-value">{radius:.2f} m</div></div>', unsafe_allow_html=True)

# 🔹 ROW 2 - EQUIPMENT (WARNA BEDA)
row2 = st.columns(4)

row2[0].markdown(f'<div class="card2"><div class="card-title">Sling</div><div class="card-value">{sling:.2f} ton</div></div>', unsafe_allow_html=True)
row2[1].markdown(f'<div class="card2"><div class="card-title">Shackle</div><div class="card-value">{shackle:.2f} ton</div></div>', unsafe_allow_html=True)
row2[2].markdown(f'<div class="card2"><div class="card-title">Hook</div><div class="card-value">{hook:.2f} ton</div></div>', unsafe_allow_html=True)
row2[3].markdown(f'<div class="card2"><div class="card-title">Crane</div><div class="card-value">{crane_input:.2f} ton</div></div>', unsafe_allow_html=True)

st.markdown("---")

# INFO CHART
st.info(f"Crane Load Chart @ {radius:.2f} m = {crane_chart:.2f} ton")

# TABLE
st.subheader("📊 Equipment Calculation")
st.dataframe(styled_df, use_container_width=True)

# SUMMARY
st.markdown("---")
st.subheader("📌 Summary")

cols = st.columns(4)

for i in range(len(df)):
    eq = df.loc[i,"Equipment"]
    stat = df.loc[i,"Status"]
    risk = df.loc[i,"Risk"]

    color = "green" if stat=="SAFE" else "red"

    cols[i].markdown(f"""
    <div class="card">
    <b>{eq}</b><br>
    Status: <span style="color:{color}">{stat}</span><br>
    Risk: {risk}
    </div>
    """, unsafe_allow_html=True)

# FINAL STATUS
st.markdown("---")

if all(df["Status"]=="SAFE"):
    st.success("✅ FINAL STATUS: SAFE")
else:
    st.error("❌ FINAL STATUS: NOT SAFE")

# WARNING
if angle > 60:
    st.warning("⚠️ Angle > 60°, risk meningkat signifikan")

if abs(cog-0.5)>0.1:
    st.warning("⚠️ COG tidak simetris")
