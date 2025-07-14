import requests, time, streamlit as st
from datetime import datetime
import pandas as pd

# API headers
HEADERS = {
    "accept": "application/json",
    "platform": "pc",
    "language": "en",
    "User-Agent": "WarframeMarketSetViewer/1.0"
}

# Map dropdown label to valid item_type(s)
CATEGORY_MAP = {
    "Warframe Sets": ["warframe"],
    "Weapon Sets": ["primary", "secondary", "melee"],
    "Arcane Sets": ["arcane"],
    "Mod Sets": ["mod"]
}

@st.cache_data(ttl=3600)
def get_all_items():
    res = requests.get("https://api.warframe.market/v1/items", headers=HEADERS, timeout=30)
    res.raise_for_status()
    return res.json()["payload"]["items"]

@st.cache_data(ttl=3600)
def get_item_info(url_name: str):
    res = requests.get(f"https://api.warframe.market/v1/items/{url_name}/item", headers=HEADERS, timeout=30)
    if res.status_code != 200:
        return None
    return res.json()["payload"]["item"]

def get_orders(url_name: str):
    res = requests.get(f"https://api.warframe.market/v1/items/{url_name}/orders", headers=HEADERS, timeout=30)
    if res.status_code != 200:
        return []
    return res.json()["payload"]["orders"]

def best_online_prices(url_name: str):
    orders = get_orders(url_name)
    online = [o for o in orders if o["user"]["status"] == "ingame"]
    sells = [o["platinum"] for o in online if o["order_type"] == "sell"]
    buys = [o["platinum"] for o in online if o["order_type"] == "buy"]
    return (min(sells) if sells else None, max(buys) if buys else None)

# ---------- Streamlit App ----------
st.set_page_config(page_title="Warframe Market Sets", page_icon="🛒", layout="wide")
st.title("🛒 Warframe.market – Set Scanner")

category = st.selectbox("Select a set category", list(CATEGORY_MAP.keys()))

with st.spinner("🔍 Loading item list..."):
    all_items = get_all_items()

# Filter to sets only (item URLs ending in '_set')
sets = [itm for itm in all_items if itm["url_name"].endswith("_set")]

wanted_types = CATEGORY_MAP[category]
filtered = []
progress = st.progress(0.0, "Filtering sets...")

for idx, itm in enumerate(sets, start=1):
    info = get_item_info(itm["url_name"])
    if info and info.get("item_type") in wanted_types:
        filtered.append(itm)
    progress.progress(idx / len(sets))
    time.sleep(0.05)

st.success(f"✅ {len(filtered)} {category.lower()} found.")

# Fetch market prices
data = []
progress2 = st.progress(0.0, "Checking live orders...")

for idx, itm in enumerate(filtered, start=1):
    low_sell, high_buy = best_online_prices(itm["url_name"])
    data.append({
        "Set": itm["item_name"],
        "Lowest WTS (p)": low_sell if low_sell else "—",
        "Highest WTB (p)": high_buy if high_buy else "—"
    })
    progress2.progress(idx / len(filtered))
    time.sleep(0.05)

df = pd.DataFrame(sorted(data, key=lambda x: x["Set"].lower()))
st.dataframe(df, use_container_width=True)

st.caption(f"Updated {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC — Prices from current online traders only.")
st.markdown(
    '<div style="text-align:right; opacity:0.5;">Made by <b>TheGame</b> · Discord: <code>Driscol#8101</code></div>',
    unsafe_allow_html=True
)
