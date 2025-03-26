import streamlit as st
import numpy as np
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from openai import OpenAI

# Establish the connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Read the data
df = conn.read(ttl=60)


#dropping the entries where there's no definition of the word in Czech
df = df.dropna(subset=["Czech"])



# Access the OpenAI API key from the secrets file
api_key = st.secrets["openai"]["api_key"]


# Set up the OpenAI API client
#openai.api_key = api_key
client = OpenAI(api_key=api_key)

# Set a default model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

tab1, tab2 = st.tabs(["Česky-Anglicky", "Anglicky-Česky"])

def sample():
    #pick a (semi) random word
    return df.sample(weights=df["probability"])

def getExample(word):
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": "user", "content": f"Napiš mi jednoduchou českou větu která užívá slovo {word}"}
            ],
            stream=True,
        )
        
    return stream
            

with tab1:
    if "sampleWord" not in st.session_state:
        st.session_state["sampleWord"] = sample()
        st.write(st.session_state["sampleWord"]["Czech"])

    

    if st.button("Nové slovíčko"):
        st.session_state["sampleWord"] = sample()
        st.write(st.session_state["sampleWord"]["Czech"])

    if st.button("Ukaž příklad"):
        st.session_state["sampleWord"] = sample()
        st.write(st.session_state["sampleWord"]["Czech"])
        st.write_stream(getExample(st.session_state["sampleWord"]["Czech"]))
        
    if st.button("Ukaž odpověd"):

        st.write(st.session_state["sampleWord"]["Czech"])
        st.write(st.session_state["sampleWord"]["English"])

    
with tab2:
    pass




