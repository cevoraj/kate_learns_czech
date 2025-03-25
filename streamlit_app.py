import streamlit as st
import numpy as np
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Establish the connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Read the data
df = conn.read(ttl=60)


#dropping the entries where there's no definition of the word in Czech
df = df.dropna(subset=["Czech"])

tab1, tab2 = st.tabs(["Česky-Anglicky", "Anglicky-Česky"])

def sample():
    #pick a (semi) random word
    return df.sample(weights=df["probability"])

            

with tab1:
    if "sampleWord" not in st.session_state:
        st.write("initializing sample")
        st.session_state["sampleWord"] = sample()
        st.write(st.session_state["sampleWord"]["Czech"])

    

    if st.button("Nové slovíčko"):
        st.session_state["sampleWord"] = sample()
        st.write(st.session_state["sampleWord"]["Czech"])
        
    if st.button("Ukaž odpověd"):
        st.write(st.session_state["sampleWord"]["Czech"])
        st.write(st.session_state["sampleWord"]["English"])

    
with tab2:

    st.write(np.random.uniform(0, 1))
    if st.button("refresh"):
        st.write("refresh")
        if st.button("new word"):
            pass
    elif st.button("show answer"):
        st.write("answer")
        if st.button("new word"):
            pass


