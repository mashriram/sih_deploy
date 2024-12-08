import streamlit as st
import pandas as pd
import requests
import plotly.graph_objs as go
import plotly.express as px
import numpy as np
from urllib.request import urlopen
import json


class CommodityDataManager:
    def __init__(self):
        # Predefined mappings for states
        self.state_mapper = {
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

        self.commodities = [
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
        ]

        self.commodities_mapper = {
            commodity.capitalize(): commodity for commodity in self.commodities
        }

    def fetch_data(self, state, commodity):
        """
        Fetch historical data from the getData endpoint
        """
        try:
            payload = {"state": state, "commodity": commodity}
            response = requests.post(
                "http://3.85.3.0:8080/krushijyotishi/getData", json=payload
            )
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

    def fetch_prediction(self, state, commodity, horizon):
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

    def fetch_prediction_for_all_states(self, commodity, horizon=150):
        """
        Fetch predictions for all states
        """
        prediction_data = {}
        commodity_lower = self.commodities_mapper[commodity]

        for state_name, state_abbr in self.state_mapper.items():
            try:
                payload = {
                    "state": state_abbr,
                    "commodity": commodity_lower,
                    "horizon": horizon,
                }
                response = requests.post(
                    "http://3.85.3.0:8080/krushijyotishi/predict", json=payload
                )

                if response.status_code == 200:
                    predictions = pd.DataFrame.from_dict(
                        response.json()["y"],
                        orient="index",
                        columns=["predicted_price"],
                    )
                    predictions.index = pd.to_datetime(predictions.index)
                    predictions.sort_index(inplace=True)

                    prediction_data[state_name] = {
                        "predictions": predictions,
                        "predicted_price": predictions["predicted_price"].iloc[0],
                    }
            except Exception as e:
                st.warning(f"Could not fetch prediction for {state_name}: {e}")

        return prediction_data


class VisualizationManager:
    @staticmethod
    def plot_results(data, prediction, commodity, state):
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
            title=f"{commodity} - {state}",
            xaxis_title="Date",
            yaxis_title="Price (Rs/Quintal)",
            height=600,
        )

        st.plotly_chart(fig)

    @staticmethod
    def create_choropleth(state_data, title):
        """
        Create an animated choropleth map of India
        """

        with urlopen(
            "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
        ) as response:
            states = json.load(response)

        # Prepare data for visualization
        state_prices = []
        for state, data in state_data.items():
            # Check for 'latest_price' in each state, if missing set to None or some default value
            if state == "Jammu  &  Kashmir and Ladakh":
                state_prices.append(
                    {"State": "Jammu & Kashmir", "Price": data["predicted_price"]}
                )
                state_prices.append(
                    {"State": "Ladakh", "Price": data["predicted_price"]}
                )
            else:
                state_prices.append({"State": state, "Price": data["predicted_price"]})

        df = pd.DataFrame(state_prices)

        # Ensure state names match exactly with the GeoJSON property (case-sensitive)
        fig = px.choropleth(
            df,
            geojson=states,
            featureidkey="properties.ST_NM",  # Ensure this matches the GeoJSON structure
            locations="State",
            color="Price",
            color_continuous_scale="Viridis",
            title=f"{title} Prices Across Indian States",
            hover_name="State",  # Show state name on hover
            hover_data=["Price"],  # Show price on hover
        )

        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            title_x=0.5,
            geo=dict(
                showframe=False, showcoastlines=True, projection_type="equirectangular"
            ),
            height=600,
        )

        return fig


def main():
    # Initialize data manager and visualization manager
    data_manager = CommodityDataManager()

    # Streamlit app layout
    st.title("Commodity Price Prediction and Visualization")
    st.write(
        "Get historical data, price predictions, and state-wise commodity price visualization."
    )

    # Visualization type selection
    viz_type = st.sidebar.radio(
        "Select Visualization Type",
        ["Line Plot (Single State)", "Choropleth Map (All States)"],
    )

    # Sidebar for user input
    selected_commodity = st.sidebar.selectbox(
        "Select Commodity", list(data_manager.commodities_mapper.keys())
    )

    if viz_type == "Line Plot (Single State)":
        # Single state line plot visualization
        selected_state = st.sidebar.selectbox(
            "Select State", list(data_manager.state_mapper.keys())
        )

        # Convert selected state to abbreviation
        state_abbr = data_manager.state_mapper[selected_state]
        commodity = data_manager.commodities_mapper[selected_commodity]

        # Prediction horizon
        horizon = st.sidebar.number_input(
            "Prediction Horizon", min_value=100, max_value=300, value=150
        )

        # Fetch data and predictions
        if st.sidebar.button("Generate Prediction"):
            with st.spinner("Fetching data and predictions..."):
                # Fetch historical data
                historical_data = data_manager.fetch_data(state_abbr, commodity)

                # Fetch predictions
                predictions = data_manager.fetch_prediction(
                    state_abbr, commodity, horizon
                )

                # Plot results
                VisualizationManager.plot_results(
                    historical_data, predictions, selected_commodity, selected_state
                )

                # Optional: Display raw data
                if st.checkbox("Show Raw Data"):
                    st.subheader("Historical Data")
                    st.dataframe(historical_data)
                    st.subheader("Predictions")
                    st.dataframe(predictions)

    else:  # Choropleth Map
        # Multiselect for states with option to select all
        all_states = list(data_manager.state_mapper.keys())
        selected_states = all_states

        # Button to generate visualization
        if st.sidebar.button("Generate Choropleth Map"):
            with st.spinner("Fetching and processing data..."):
                try:
                    # Fetch state-wise commodity data
                    state_data = data_manager.fetch_prediction_for_all_states(
                        selected_commodity
                    )
                    print(state_data)
                    default_state_data = {
                        state: {"predicted_price": 0} for state in all_states
                    }

                    # Merge the fetched data with the default data
                    filtered_state_data = {
                        state: state_data.get(state, default_state_data[state])
                        for state in selected_states
                    }
                    # Create and display choropleth map
                    choropleth_fig = VisualizationManager.create_choropleth(
                        filtered_state_data, selected_commodity
                    )
                    st.plotly_chart(choropleth_fig)

                    # Optional: Show detailed data
                    if st.checkbox("Show Detailed State Prices"):
                        price_df = pd.DataFrame(
                            [
                                {
                                    "State": state,
                                    "Latest Price (Rs/Quintal)": data["latest_price"],
                                }
                                for state, data in filtered_state_data.items()
                            ]
                        )
                        st.dataframe(price_df)

                except Exception as e:
                    st.error(f"Error generating visualization: {e}")


if __name__ == "__main__":
    main()
