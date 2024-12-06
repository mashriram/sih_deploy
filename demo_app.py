import streamlit as st
from darts.models import NBEATSModel

nbeats = NBEATSModel.load("./nbeats_model.pt")
df = nbeats.predict(15)
st.write("Forecast")
st.write(df.to_json())
