import requests
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from dateutil import parser

# Set page config with a more modern, wide layout
st.set_page_config(page_title="Warframe Market Explorer", page_icon="🛒", layout="wide")

# ---------------------------------------------
# CSS for a watermark and a more modern feel
st.markdown("""
<style>
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

h1, h2, h3, h4, h5 {
    font-family: 'Helvetica Neue', sans-serif;
    color: #333;
}

.sidebar .stSelectbox label {
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# Add Watermark
st.markdown(
    '<div class="watermark">Made by TheGame / discord: Driscol#8101</div>',
    unsafe_allow_html=True
)

# Main Title
st.title("Warframe Market Data Explorer")

# ---------------------------------------------
# Functions

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

def get_profitable_items():
    # In a real scenario, implement logic to:
    # 1. Fetch multiple items stats (e.g., from a cached dataset).
    # 2. Calculate potential profit (sell price - buy price).
    # 3. Consider volume (only show items with high volume).
    # 4. Return top picks by profit margin and volume.
    
    # Below is a mock dataset for demonstration:
    mock_items = [
        {"name": "Volt Prime Chassis", "buy_price": 10, "sell_price": 15, "profit": 5, "volume": 120},
        {"name": "Ash Prime Systems", "buy_price": 20, "sell_price": 28, "profit": 8, "volume": 95},
        {"name": "Rhino Prime Neuroptics", "buy_price": 6, "sell_price": 10, "profit": 4, "volume": 200},
        {"name": "Nova Prime Blueprint", "buy_price": 50, "sell_price": 65, "profit": 15, "volume": 30},
        {"name": "Loki Prime Systems", "buy_price": 35, "sell_price": 50, "profit": 15, "volume": 150},
    ]
    # Sort by profit and volume for demonstration
    mock_items.sort(key=lambda x: (x["profit"], x["volume"]), reverse=True)
    return mock_items[:5]

# ---------------------------------------------
# Get all items for the dropdown
item_options = get_all_items()
item_names = [i[0] for i in item_options]
item_url_map = {name: url_name for name, url_name in item_options}

# Layout: left for main charts, right for profit suggestions
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

                    for d, p, v in zip(dates, avg_prices, volumes):
                        if date_range[0] <= d.date() <= date_range[1]:
                            filtered_dates.append(d)
                            filtered_prices.append(p)
                            filtered_volumes.append(v)

                    # Display charts
                    st.subheader(f"Market Trends for {selected_item}")
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
    st.markdown("### Top Profit Opportunities")
    st.write("Based on current market prices and volume, here are some items that might yield a good profit margin:")

    profitable_items = get_profitable_items()
    # Display each item in a nice format
    for pi in profitable_items:
        st.markdown(f"**{pi['name']}**")
        st.write(f"Buy: {pi['buy_price']}p | Sell: {pi['sell_price']}p | Profit: {pi['profit']}p | Volume: {pi['volume']}")
        st.markdown("---")
    
    st.markdown("**Note:** This is an example. In a real application, this section would dynamically fetch multiple items from the Warframe Market API, calculate actual buy/sell spreads, consider volume, and pick the best flipping candidates.")
