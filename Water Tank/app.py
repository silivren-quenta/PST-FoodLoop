import streamlit as st
from water_tank import get_pump_status, get_water_amount

st.set_page_config(
    page_title="Smart Water Tank",
    page_icon="💧",
    layout="centered"
)

st.title("💧 Smart Water Tank")
st.write("Intelligent Water Resource Management System")

st.divider()

water_level = st.slider(
    "Water Level",
    min_value=0,
import streamlit as st
from water_tank 
import get_pump_status, get_water_amount

st.set_page_config(
    page_title="Smart Water Tank",
    page_icon="💧",
    layout="centered"
)

st.title("💧 Smart Water Tank")
st.write("Intelligent Water Resource Management System")

st.divider()

water_level = st.slider(
    "Water Level",
    min_value=0,
    max_value=100,
    value=50,
    step=1
)

pump_status = get_pump_status(water_level)
water_amount = get_water_amount(water_level)

st.subheader("Tank Status")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Water Level", f"{water_level}%")

with col2:
    st.metric("Water Stored", f"{water_amount:.0f} L")

with col3:
    st.metric("Pump", pump_status)

st.divider()

if water_level <= 30:
    st.error("⚠️ Water level is LOW")
    st.info("🚰 Pump automatically turned ON")

elif water_level >= 90:
    st.success("✅ Tank is FULL")
    st.warning("🛑 Pump automatically turned OFF")

else:
    st.info("💧 Water level is normal")
    st.info("🚰 Pump is running")

st.subheader("Tank")

tank_height = 300
filled_height = int((water_level / 100) * tank_height)

st.markdown(
    f"""
    <div style="
        width:250px;
        height:{tank_height}px;
        border:5px solid black;
        border-radius:15px;
        margin:auto;
        position:relative;
        overflow:hidden;
        background:#f0f0f0;
    ">
        <div style="
            position:absolute;
            bottom:0;
            width:100%;
            height:{filled_height}px;
            background:#2196F3;
        "></div>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

st.subheader("System Logic")

st.write("""
- Water level below **30%** → Pump ON
- Water level between **30% and 90%** → Normal operation
- Water level reaches **90%** → Pump OFF
- This prevents water overflow and reduces unnecessary water and electricity consumption.
""")
    max_value=100,
    value=50,
    step=1
)

pump_status = get_pump_status(water_level)
water_amount = get_water_amount(water_level)

st.subheader("Tank Status")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Water Level", f"{water_level}%")

with col2:
    st.metric("Water Stored", f"{water_amount:.0f} L")

with col3:
    st.metric("Pump", pump_status)

st.divider()

if water_level <= 30:
    st.error("⚠️ Water level is LOW")
    st.info("🚰 Pump automatically turned ON")

elif water_level >= 90:
    st.success("✅ Tank is FULL")
    st.warning("🛑 Pump automatically turned OFF")

else:
    st.info("💧 Water level is normal")
    st.info("🚰 Pump is running")

st.subheader("Tank")

tank_height = 300
filled_height = int((water_level / 100) * tank_height)

st.markdown(
    f"""
    <div style="
        width:250px;
        height:{tank_height}px;
        border:5px solid black;
        border-radius:15px;
        margin:auto;
        position:relative;
        overflow:hidden;
        background:#f0f0f0;
    ">
        <div style="
            position:absolute;
            bottom:0;
            width:100%;
            height:{filled_height}px;
            background:#2196F3;
        "></div>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

st.subheader("System Logic")

st.write("""
- Water level below **30%** → Pump ON
- Water level between **30% and 90%** → Normal operation
- Water level reaches **90%** → Pump OFF
- This prevents water overflow and reduces unnecessary water and electricity consumption.
""")