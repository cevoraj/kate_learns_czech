import streamlit as st


from streamlit_gsheets import GSheetsConnection

# Establish the connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Read the data
df = conn.read()

# Display the data
for row in df.itertuples():
    st.write(f"{row}")


st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)
