import requests
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from dateutil import parser

# Set page config (optional)
st.set_page_config(page_title="Warframe Market Explorer", page_icon="🛒", layout="wide")

st.title("Warframe Market Data Explorer")

# ---------------------------------------------
# 1. Fetch the list of items from Warframe Market API
@st.cache_data(show_spinner=False)
def get_all_items():
    # Get all items
    url = "https://api.warframe.market/v1/items"
    headers = {
        "Language": "en",
        "User-Agent": "WarframeMarketApp/1.0"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        items = data["payload"]["items"]
        # Extract (item_name, url_name) tuples for searching
        item_options = [(item["item_name"], item["url_name"]) for item in items if item["item_name"]]
        # Sort by name
        item_options.sort(key=lambda x: x[0].lower())
        return item_options
    else:
        st.error("Failed to fetch item list. Please try again later.")
        return []

item_options = get_all_items()
item_names = [i[0] for i in item_options]
item_url_map = {name: url_name for name, url_name in item_options}

# ---------------------------------------------
# 2. Select an item using a search box
selected_item = st.selectbox("Search and select an item", options=item_names)

if selected_item:
    # ---------------------------------------------
    # 3. Fetch statistics for the selected item
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

    item_url_name = item_url_map[selected_item]
    stats_data = get_item_stats(item_url_name)

    if stats_data:
        # The data is usually in stats_data["payload"]["statistics_closed"]
        # These often include periods like "48hours", "90days", etc.
        # We'll focus on the "90days" data as an example.
        closed_stats = stats_data["payload"]["statistics_closed"]
        # Check available periods
        periods = list(closed_stats.keys())
        period_choice = st.selectbox("Select a timeframe", periods)
        
        if period_choice in closed_stats:
            time_data = closed_stats[period_choice]

            # Convert the stats into lists
            dates = [parser.parse(entry["datetime"]) for entry in time_data]
            avg_prices = [entry["avg_price"] for entry in time_data]
            volumes = [entry["volume"] for entry in time_data]

            # ---------------------------------------------
            # 4. Add a slider to filter the visible date range
            if len(dates) > 0:
                min_date, max_date = min(dates), max(dates)
                # Convert dates to just date for easier sliding
                date_range = st.slider("Select date range", min_value=min_date.date(), max_value=max_date.date(), value=(min_date.date(), max_date.date()))
                
                # Filter data based on slider
                filtered_dates = []
                filtered_prices = []
                filtered_volumes = []
                
                for d, p, v in zip(dates, avg_prices, volumes):
                    if date_range[0] <= d.date() <= date_range[1]:
                        filtered_dates.append(d)
                        filtered_prices.append(p)
                        filtered_volumes.append(v)
                
                # ---------------------------------------------
                # 5. Display the graphs using Plotly
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Average Price Over Time")
                    fig_price = go.Figure()
                    fig_price.add_trace(go.Scatter(x=filtered_dates, y=filtered_prices, mode='lines+markers', name='Avg Price', line=dict(color='blue')))
                    fig_price.update_layout(xaxis_title="Date", yaxis_title="Price (Platinum)", template='plotly_white')
                    st.plotly_chart(fig_price, use_container_width=True)

                with col2:
                    st.subheader("Volume Over Time")
                    fig_volume = go.Figure()
                    fig_volume.add_trace(go.Scatter(x=filtered_dates, y=filtered_volumes, mode='lines+markers', name='Volume', line=dict(color='green')))
                    fig_volume.update_layout(xaxis_title="Date", yaxis_title="Volume", template='plotly_white')
                    st.plotly_chart(fig_volume, use_container_width=True)

                # Show a summary at the bottom
                st.write(f"**Selected Range:** {date_range[0]} - {date_range[1]}")
                st.write(f"**Total Entries:** {len(filtered_dates)}")
                
            else:
                st.warning("No data available for this item/timeframe.")
        else:
            st.warning("Selected timeframe data not available.")
