import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go


def fetch_data(state, commodity):
    """
    Fetch data from the getData endpoint
    """
    try:
        payload = {"state": state, "commodity": commodity}
        response = requests.post(
            "http://3.85.3.0:8080/krushijyotishi/getData", json=payload
        )
        print("response", response)
        if response.status_code == 200:
            # Parse the nested JSON structure
            data = pd.DataFrame.from_dict(
                response.json()["modal_rs_quintal"],
                orient="index",
                columns=["modal_rs_quintal"],
            )
            data.index = pd.to_datetime(data.index)
            data.sort_index(inplace=True)
            return data
        else:
            st.error(f"Error fetching data: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Exception in data fetching: {e}")
        return pd.DataFrame()


def fetch_prediction(state, commodity, horizon):
    """
    Fetch predictions from the predict endpoint
    """
    try:
        payload = {"state": state, "commodity": commodity, "horizon": horizon}
        response = requests.post(
            "http://3.85.3.0:8080/krushijyotishi/predict", json=payload
        )
        if response.status_code == 200:
            # Parse the nested JSON structure for predictions
            predictions = pd.DataFrame.from_dict(
                response.json()["y"], orient="index", columns=["predicted_price"]
            )
            predictions.index = pd.to_datetime(predictions.index)
            predictions.sort_index(inplace=True)
            return predictions
        else:
            st.error(f"Error fetching predictions: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Exception in prediction fetching: {e}")
        return None


def plot_results(data, prediction):
    """
    Create Plotly chart with historical data and predictions
    """
    if data.empty or prediction is None:
        st.write("No data available to plot")
        return

    fig = go.Figure()

    # Historical data
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["modal_rs_quintal"],
            mode="lines",
            name="Historical Data",
        )
    )

    # Predictions
    fig.add_trace(
        go.Scatter(
            x=prediction.index,
            y=prediction["predicted_price"],
            mode="lines",
            name="Prediction",
        )
    )

    fig.update_layout(
        title=f"{selected_commodity} - {selected_state}",
        xaxis_title="Date",
        yaxis_title="Price (Rs/Quintal)",
        height=600,
    )

    st.plotly_chart(fig)


# Predefined mappings for states
state_mapper = {
    "Arunachal Pradesh": "AR",
    "Andaman & Nicobar": "AN",
    "Andhra Pradesh": "AP",
    "Assam": "AS",
    "Bihar": "BI",
    "Chhattisgarh": "CG",
    "Delhi": "DL",
    "Chandigarh": "CH",
    "Goa": "GO",
    "Gujarat": "GJ",
    "Haryana": "HR",
    "Himachal Pradesh": "HP",
    "Jharkhand": "JR",
    "Jammu  &  Kashmir and Ladakh": "JK",
    "Karnataka": "KK",
    "Kerala": "KL",
    "Madhya Pradesh": "MP",
    "Maharashtra": "MH",
    "Manipur": "MN",
    "Meghalaya": "MG",
    "Mizoram": "MZ",
    "Nagaland": "NG",
    "Odisha": "OR",
    "Punjab": "PB",
    "Rajasthan": "RJ",
    "Sikkim": "SK",
    "Tamil Nadu": "TN",
    "Telangana": "TL",
    "Tripura": "TR",
    "Uttarakhand": "UC",
    "Uttar Pradesh": "UP",
    "West Bengal": "WB",
}

# Streamlit app layout
st.title("Commodity Price Prediction")
st.write(
    "Get historical data and 10-day price predictions for different commodities and states."
)

# Sidebar inputs
commodities = [
    "Gram dal",
    "Groundnut oil",
    "gur",
    "masur dal",
    "moong dal",
    "mustard oil",
    "onion",
    "Potato",
    "Rice",
    "Sugar",
    "tea",
    "tomato",
    "tur dal",
    "urad dal",
    "vanaspati",
    "wheat",
]  # Add more as needed
commodities_mapper: dict[str, str] = {
    commodity.capitalize(): commodity for commodity in commodities
}
# Sidebar for user input
selected_commodity = st.sidebar.selectbox(
    "Select Commodity", list(commodities_mapper.keys())
)
selected_state = st.sidebar.selectbox("Select State", list(state_mapper.keys()))

# Convert selected state to abbreviation
state_abbr = state_mapper[selected_state]
commodity = commodities_mapper[selected_commodity]

# Prediction horizon
horizon = st.sidebar.number_input(
    "Prediction Horizon", min_value=100, max_value=300, value=150
)

# Fetch data and predictions
if st.sidebar.button("Generate Prediction"):
    with st.spinner("Fetching data and predictions..."):
        # Fetch historical data
        historical_data = fetch_data(state_abbr, commodity)

        # Fetch predictions
        predictions = fetch_prediction(state_abbr, commodity, horizon)

        # Plot results
        plot_results(historical_data, predictions)

# Optional: Display raw data
if st.checkbox("Show Raw Data"):
    if "historical_data" in locals():
        st.subheader("Historical Data")
        st.dataframe(historical_data)
    if "predictions" in locals():
        st.subheader("Predictions")
        st.dataframe(predictions)
