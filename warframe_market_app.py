import requests
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from dateutil import parser

st.set_page_config(page_title="Warframe Market Explorer", page_icon="🛒", layout="wide")

# ---------------------------------------------
# CSS for improved look and watermark
st.markdown("""
<style>
body {
    font-family: 'Helvetica Neue', sans-serif;
    color: #333;
}

/* Watermark in the bottom-right corner */
.watermark {
    position: fixed;
    bottom: 10px;
    right: 10px;
    font-size: 12px;
    color: #999;
    opacity: 0.8;
    z-index: 9999;
}

/* Header image styling */
.header-container {
    display: flex;
    align-items: center;
    gap: 10px;
}
.header-logo {
    width: 40px;
    height: 40px;
    object-fit: contain;
}

/* Make side sections more distinct */
.sidebar-section {
    background: #f9f9f9;
    padding: 10px;
    border-radius: 5px;
    margin-bottom: 20px;
}

/* Item row styling */
.item-row {
    display: flex;
    align-items: center;
    gap: 10px;
}
.item-row img {
    width: 24px;
    height: 24px;
    object-fit: contain;
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)

# Add Watermark
st.markdown(
    '<div class="watermark">Made by TheGame / discord: Driscol#8101</div>',
    unsafe_allow_html=True
)

# ---------------------------------------------
# Load images (Make sure these files exist in the images folder in your GitHub repo)
def get_image_base64(path):
    # In a real scenario, you can handle exceptions if the image is missing.
    import base64
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

# Display a header with a logo (make sure "warframe_logo.png" is in images/)
col_logo, col_title = st.columns([0.1, 0.9])
with col_logo:
    # Display logo if exists
    st.image("images/warframe_logo.png", width=50)
with col_title:
    st.title("Warframe Market Data Explorer")

# ---------------------------------------------
@st.cache_data(show_spinner=False)
def get_all_items():
    url = "https://api.warframe.market/v1/items"
    headers = {
        "Language": "en",
        "User-Agent": "WarframeMarketApp/1.0"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        items = data["payload"]["items"]
        item_options = [(item["item_name"], item["url_name"]) for item in items if item["item_name"]]
        item_options.sort(key=lambda x: x[0].lower())
        return item_options
    else:
        st.error("Failed to fetch item list. Please try again later.")
        return []

@st.cache_data(show_spinner=False)
def get_item_stats(item_url_name):
    url = f"https://api.warframe.market/v1/items/{item_url_name}/statistics"
    headers = {
        "Language": "en",
        "User-Agent": "WarframeMarketApp/1.0"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch item statistics.")
        return None

def get_profitable_items(sort_by="profit"):
    # Mock data: In a real scenario, fetch and calculate dynamically
    mock_items = [
        {"name": "Volt Prime Chassis", "buy_price": 10, "sell_price": 15, "profit": 5, "volume": 120, "icon": "icon_item_volt_prime.png"},
        {"name": "Ash Prime Systems", "buy_price": 20, "sell_price": 28, "profit": 8, "volume": 95, "icon": "icon_item_ash_prime_systems.png"},
        {"name": "Rhino Prime Neuroptics", "buy_price": 6, "sell_price": 10, "profit": 4, "volume": 200, "icon": "icon_item_rhino_prime_neuroptics.png"},
        {"name": "Nova Prime Blueprint", "buy_price": 50, "sell_price": 65, "profit": 15, "volume": 30, "icon": "icon_item_nova_prime_blueprint.png"},
        {"name": "Loki Prime Systems", "buy_price": 35, "sell_price": 50, "profit": 15, "volume": 150, "icon": "icon_item_loki_prime_systems.png"},
    ]
    if sort_by == "profit":
        mock_items.sort(key=lambda x: x["profit"], reverse=True)
    elif sort_by == "volume":
        mock_items.sort(key=lambda x: x["volume"], reverse=True)

    return mock_items[:5]

def get_trending_items():
    # Mock data: In a real scenario, analyze recent data to find trending items
    trending = [
        {"name": "Frost Prime Neuroptics", "direction": "up", "icon": "icon_item_frost_prime_neuroptics.png"},
        {"name": "Ember Prime Blueprint", "direction": "down", "icon": "icon_item_ember_prime_blueprint.png"},
        {"name": "Hydroid Prime Systems", "direction": "stable", "icon": "icon_item_hydroid_prime_systems.png"}
    ]
    return trending

# ---------------------------------------------
item_options = get_all_items()
item_names = [i[0] for i in item_options]
item_url_map = {name: url_name for name, url_name in item_options}

col_main, col_side = st.columns([3,1])

with col_main:
    selected_item = st.selectbox("🔍 Search and select an item", options=item_names)

    if selected_item:
        item_url_name = item_url_map[selected_item]
        stats_data = get_item_stats(item_url_name)

        if stats_data and "payload" in stats_data and "statistics_closed" in stats_data["payload"]:
            closed_stats = stats_data["payload"]["statistics_closed"]
            periods = list(closed_stats.keys())
            period_choice = st.selectbox("Select a timeframe", periods)

            if period_choice in closed_stats:
                time_data = closed_stats[period_choice]

                dates = [parser.parse(entry["datetime"]) for entry in time_data]
                avg_prices = [entry["avg_price"] for entry in time_data]
                volumes = [entry["volume"] for entry in time_data]

                if len(dates) > 0:
                    min_date, max_date = min(dates), max(dates)
                    date_range = st.slider("Select date range", 
                                           min_value=min_date.date(), 
                                           max_value=max_date.date(), 
                                           value=(min_date.date(), max_date.date()))
                    
                    filtered_dates = []
                    filtered_prices = []
                    filtered_volumes = []

                    # Simple logic to determine direction of price change
                    price_change_indicator = "stable"
                    if len(avg_prices) > 1:
                        if avg_prices[-1] > avg_prices[-2]:
                            price_change_indicator = "up"
                        elif avg_prices[-1] < avg_prices[-2]:
                            price_change_indicator = "down"

                    # Load direction icons (make sure they exist)
                    direction_icons = {
                        "up": "images/arrow_up.png",
                        "down": "images/arrow_down.png",
                        "stable": "images/arrow_stable.png"
                    }

                    for d, p, v in zip(dates, avg_prices, volumes):
                        if date_range[0] <= d.date() <= date_range[1]:
                            filtered_dates.append(d)
                            filtered_prices.append(p)
                            filtered_volumes.append(v)

                    st.subheader(f"Market Trends for {selected_item}")
                    st.image(direction_icons[price_change_indicator], width=20)

                    chart_col1, chart_col2 = st.columns(2)
                    with chart_col1:
                        st.markdown("**Average Price Over Time**")
                        fig_price = go.Figure()
                        fig_price.add_trace(
                            go.Scatter(
                                x=filtered_dates, 
                                y=filtered_prices, 
                                mode='lines+markers',
                                line=dict(color='blue'),
                                name='Avg Price'
                            )
                        )
                        fig_price.update_layout(
                            xaxis_title="Date", 
                            yaxis_title="Price (Platinum)",
                            template='plotly_white',
                            hovermode='x unified'
                        )
                        st.plotly_chart(fig_price, use_container_width=True)

                    with chart_col2:
                        st.markdown("**Volume Over Time**")
                        fig_volume = go.Figure()
                        fig_volume.add_trace(
                            go.Scatter(
                                x=filtered_dates, 
                                y=filtered_volumes, 
                                mode='lines+markers', 
                                line=dict(color='green'),
                                name='Volume'
                            )
                        )
                        fig_volume.update_layout(
                            xaxis_title="Date", 
                            yaxis_title="Volume",
                            template='plotly_white',
                            hovermode='x unified'
                        )
                        st.plotly_chart(fig_volume, use_container_width=True)

                    st.write(f"**Selected Range:** {date_range[0]} - {date_range[1]}")
                    st.write(f"**Total Data Points:** {len(filtered_dates)}")

                else:
                    st.warning("No data available for this item/timeframe.")
            else:
                st.warning("Selected timeframe data not available.")
        else:
            st.warning("No statistics found for this item.")

with col_side:
    st.markdown("### Best Profit Opportunities")
    st.write("Pick a sorting option to find your best flip targets:")
    sort_choice = st.selectbox("Sort by", ["profit", "volume"])

    profitable_items = get_profitable_items(sort_by=sort_choice)

    side_section = st.container()
    with side_section:
        for pi in profitable_items:
            # Display item row with icon
            st.markdown('<div class="item-row">', unsafe_allow_html=True)
            st.image("images/" + pi["icon"], width=24)
            st.markdown(f"**{pi['name']}**<br>Buy: {pi['buy_price']}p | Sell: {pi['sell_price']}p | Profit: {pi['profit']}p | Vol: {pi['volume']}", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")

    # Add a trending items section
    st.markdown("### Trending Items")
    st.write("Items with recent upward or downward price movement:")
    trending_items = get_trending_items()
    for ti in trending_items:
        st.markdown('<div class="item-row">', unsafe_allow_html=True)
        st.image("images/" + ti["icon"], width=24)
        direction_icon = f"images/arrow_{ti['direction']}.png"
        st.markdown(f"**{ti['name']}** <img src='{direction_icon}' width='20' style='vertical-align:middle;'>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("#### Note:")
    st.write("Trending items are based on recent price movement. In a real app, this would be dynamically calculated.")

