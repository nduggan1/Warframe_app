import requests, time, streamlit as st
from datetime import datetime
import pandas as pd

HEADERS = {
    "accept": "application/json",
    "platform": "pc",
    "language": "en",
    "User-Agent": "WarframeMarketSetFlipper/1.0"
}

@st.cache_data(ttl=3600)
def get_all_items():
    r = requests.get("https://api.warframe.market/v1/items", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()["payload"]["items"]

def get_item_info(url_name: str):
    r = requests.get(f"https://api.warframe.market/v1/items/{url_name}/item", headers=HEADERS, timeout=30)
    if r.status_code != 200:
        return None
    return r.json()["payload"]["item"]

def get_orders(url_name: str):
    r = requests.get(f"https://api.warframe.market/v1/items/{url_name}/orders", headers=HEADERS, timeout=30)
    if r.status_code != 200:
        return []
    return r.json()["payload"]["orders"]

def get_lowest_online_sell(orders):
    sells = [o["platinum"] for o in orders if o["order_type"] == "sell" and o["user"]["status"] == "ingame"]
    return min(sells) if sells else None

def count_online_sellers(orders):
    return sum(1 for o in orders if o["order_type"] == "sell" and o["user"]["status"] == "ingame")

# App
st.set_page_config(page_title="Warframe Flipping Scanner", page_icon="💰", layout="wide")
st.title("💰 Prime Set Flip Finder — Warframe.market")
st.caption("Optimized to help you buy low and sell high in-game. Focused on Warframe Prime sets only.")

with st.spinner("Fetching Warframe Prime sets…"):
    items = get_all_items()
    # Only _set items with warframe names
    warframe_sets = [itm for itm in items if itm["url_name"].endswith("_set") and any(
        wf in itm["item_name"].lower() for wf in [
            "ash", "atlas", "banshee", "chroma", "ember", "equinox", "excalibur", "frost",
            "gara", "garuda", "harrow", "hydroid", "inaros", "ivara", "khora", "limbo",
            "loki", "mesa", "mirage", "nekros", "nezha", "nidus", "nova", "nyx", "oberon",
            "octavia", "protea", "rhino", "saryn", "titania", "trinity", "valkyr", "vauban",
            "volt", "wisp", "wukong", "xaku", "zephyr"
        ])
    ]

results = []
progress = st.progress(0.0)
for idx, item in enumerate(warframe_sets, start=1):
    url_name = item["url_name"]
    orders = get_orders(url_name)
    price = get_lowest_online_sell(orders)
    sellers_online = count_online_sellers(orders)
    info = get_item_info(url_name)

    if not price or not info:
        continue

    # Get sell volume from statistics
    volume = 0
    stats = info.get("statistics", {}).get("48hours") or []
    if not stats:
        stats = info.get("statistics", {}).get("90days", [])
    if stats:
        volume = sum(d["volume"] for d in stats[-10:]) // len(stats[-10:]) if stats else 0

    flip_score = round((volume * 100) / (price + 1), 2)

    results.append({
        "Set": item["item_name"],
        "Lowest WTS (p)": price,
        "Online Sellers": sellers_online,
        "Avg Daily Volume": volume,
        "Flip Score": flip_score
    })
    progress.progress(idx / len(warframe_sets))
    time.sleep(0.05)

df = pd.DataFrame(sorted(results, key=lambda x: x["Flip Score"], reverse=True))
st.dataframe(df, use_container_width=True)

st.caption(f"Updated {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
st.markdown('<div style="text-align:right; opacity:0.5;">Made by <b>TheGame</b> · Discord: <code>Driscol#8101</code></div>', unsafe_allow_html=True)
