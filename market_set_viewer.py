import requests, time, streamlit as st
from datetime import datetime
import pandas as pd

HEADERS = {
    "accept": "application/json",
    "platform": "pc",
    "language": "en",
    "User-Agent": "WarframeMarketSetViewer/1.3"
}

# Only two valid categories with actual sets
CATEGORY_MAP = {
    "Warframe Sets": lambda name: any(wf in name.lower() for wf in [
        "ash", "atlas", "banshee", "chroma", "ember", "equinox", "excalibur", "frost",
        "gara", "garuda", "harrow", "hydroid", "inaros", "ivara", "khora", "limbo",
        "lok", "mesa", "mirage", "nekros", "nezha", "nidus", "nova", "nyx", "oberon",
        "octavia", "protea", "rhino", "saryn", "titania", "trinity", "valkyr", "vauban",
        "volt", "wisp", "wukong", "xaku", "zephyr"
    ]),
    "Weapon Sets": lambda name: True  # Catch all remaining sets as weapons
}

@st.cache_data(ttl=3600)
def get_all_items():
    res = requests.get("https://api.warframe.market/v1/items", headers=HEADERS, timeout=30)
    res.raise_for_status()
    return res.json()["payload"]["items"]

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
st.title("🛒 Warframe.market – Prime Set Scanner")

category = st.selectbox("Select a category", list(CATEGORY_MAP.keys()))
is_match = CATEGORY_MAP[category]

with st.spinner("🔍 Loading items…"):
    all_items = get_all_items()
    set_items = [itm for itm in all_items if itm["url_name"].endswith("_set")]

    # Smart filtering
    if category == "Weapon Sets":
        filtered = [itm for itm in set_items if not CATEGORY_MAP["Warframe Sets"](itm["item_name"])]
    else:
        filtered = [itm for itm in set_items if is_match(itm["item_name"])]

if not filtered:
    st.error("❌ No matching sets found. Try another category.")
    st.stop()

st.success(f"✅ Found {len(filtered)} {category.lower()}.")

# Get prices
data = []
progress = st.progress(0.0, "Checking live market prices...")

for idx, itm in enumerate(filtered, start=1):
    low_sell, high_buy = best_online_prices(itm["url_name"])
    data.append({
        "Set": itm["item_name"],
        "Lowest WTS (p)": low_sell if low_sell else "—",
        "Highest WTB (p)": high_buy if high_buy else "—"
    })
    progress.progress(idx / len(filtered))
    time.sleep(0.05)

df = pd.DataFrame(sorted(data, key=lambda x: x["Set"].lower()))
st.dataframe(df, use_container_width=True)

st.caption(f"Updated {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC — Prices from current online traders only.")
st.markdown(
    '<div style="text-align:right; opacity:0.5;">Made by <b>TheGame</b> · Discord: <code>Driscol#8101</code></div>',
    unsafe_allow_html=True
)
