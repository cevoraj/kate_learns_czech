import streamlit as st
import numpy as np
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from openai import OpenAI
import json


fullExample = ""

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
    st.session_state["openai_model"] = "gpt-4o"

tab1, tab2 = st.tabs(["Česky-Anglicky", "Anglicky-Česky"])

def sample():
    #pick a (semi) random word
    return df.sample(weights=df["probability"])

def getExample(word):
    global fullExample

    message = client.chat.completions.create(
        model=st.session_state["openai_model"],
        messages=[
            {"role": "user", "content": f"Napiš mi jednoduchou českou větu která užívá slovo {word}. Věta by měla mít maximálně 8 slov a  měla by jen používat jednoduché gramatické koncepty vhodné pro studenta českého jazyku na úrovní B1. Slovo {word} by mělo být podtrženo markdownem."},
        ],
    )
    return message.choices[0].message.content

def getTranslation(text):
    message = client.chat.completions.create(
        model=st.session_state["openai_model"],
        messages=[
            {"role": "user", "content": f"Přelož mi tuto větu do angličtiny: {text}"},
        ],
    )
        
    return message.choices[0].message.content
            

with tab1:
    if "sampleWord" not in st.session_state:
        st.session_state["sampleWord"] = sample()
    if "state" not in st.session_state:
        st.session_state["state"] = "init"
    
    

    if st.button("Nové slovíčko"):
        st.session_state["sampleWord"] = sample()
        st.session_state["state"] = "new"

    st.write(st.session_state["sampleWord"]["Czech"].values[0])

    if st.button("Ukaž příklad"):
        example = getExample(st.session_state["sampleWord"]["Czech"].values[0])
        st.session_state["example"] = example

        st.session_state["state"] = "example"
    
    if st.session_state["state"] == "example":
        st.write(st.session_state["example"])
        
        
    if st.button("Ukaž odpověd"):
        st.write(st.session_state["sampleWord"]["English"].values[0])
        if st.session_state["state"] == "example":
            st.write(getTranslation(st.session_state["example"]))
        
        st.session_state["state"] = "answer"

    
with tab2:
    pass




