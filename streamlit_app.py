import streamlit as st
import numpy as np
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from openai import OpenAI
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json


# Define the scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

def namespace_to_dict(namespace):
    return {k: v for k, v in vars(namespace).items()}

gcpCreds = st.secrets["gcp"]

# Authorize the client
client = gspread.service_account_from_dict(gcpCreds)

# Open the Google Sheet
sheet = client.open('Slovnicek')
worksheet = sheet.worksheet('Sheet1')

# Read or write data
df = pd.DataFrame(worksheet.get_all_records())

worksheetDeclination = sheet.worksheet('Sheet2')
# Read or write data
df_declination = pd.DataFrame(worksheetDeclination.get_all_records())





def updateSheet(df,sheet):
    # Convert DataFrame to a list of lists
    data = [df.columns.values.tolist()] + df.values.tolist()

    # Clear the existing content in the sheet
    sheet.clear()

    # Update the sheet with the DataFrame
    sheet.update('A1', data)


# Access the OpenAI API key from the secrets file
api_key = st.secrets["openai"]["api_key"]


# Set up the OpenAI API client
#openai.api_key = api_key
client = OpenAI(api_key=api_key)

# Set a default model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o"

def ask(txt):
    message = client.chat.completions.create(
        model=st.session_state["openai_model"],
        messages=[
            {"role": "user", "content": txt},
        ],
    )
    return message.choices[0].message.content

def getDeclination(word,sentence):
    txt = ask(f" v této větě: '{sentence}'. Je použito slovo '{word}'. Vygeneruj tři alternativní skloňování nebo časování tohoto slova, které budou v kontextu vět špatně. Ve své odpovědi uveď prvně správné znění slova (tak jak bylo správně použito, ale bez zbytku věty), pak středník a potom ty tři špatné skloňování nebo časování také oddělené středníkem.")
    txt = txt.replace(".","")
    options = txt.split(";")
    return options

def explainDeclination(sentence, word):
    return ask(f"V této větě: '{sentence}'. Je použito slovo '{word}'. Vysvětli proč je toto slovo v této větě použito v tomto tvaru. Vysvětli Anglicky jaké gramatické pravidlo se zde uplatňuje a proč. Use English. Keep your explanation succint, max 20 words.")

def blankWordOut(sentence,word):
    return ask(f"Ve větě '{sentence}' je použito slovo '{word}'. Nahraď celé toto slovo (včetně potenciálního skloňování nebo časování) podtržítky. Nevracej žádný jiný text než větu s podtržítky místo původního slova.")

def randomiseOptions(options):
    options = np.array(options)
    indices = np.random.permutation(4)
    return options[indices]

def sample(df):
    #pick a (semi) random word
    smpl = df.sample(weights=df["probability"])
    return smpl, smpl.index 

def getExample(word,case="jakémkoliv"):
    return ask(f"Napiš mi jednoduchou českou větu která užívá slovo '{word}'. Pokud je slovo '{word}' podstatným jménem tak jej věta musí použít v {case}. pádě. Věta by měla mít maximálně 8 slov a  měla by jen používat jednoduché gramatické koncepty vhodné pro studenta českého jazyku na úrovní B1. Slovo '{word}' by mělo být podtrženo markdownem.")

def getTranslation(text,direction="cs-en"):
    if direction == "cs-en":
        return ask(f"Přelož mi tuto větu do angličtiny: '{text}'")
    else:
        return ask(f"Přelož mi tuto větu do češtiny: '{text}'")
            
def detectCase(word,sentence):
    txt = ask(f"V této větě: '{sentence}'. Je použito slovo '{word}'. Jaký pád je použit pro toto slovo? Odpověz pouze číslem 1-7. Pokud slovo není podstatné jméno, tak odpověz '0'.")
    return txt

def updateCase(case,correct,sheetDeclination,sheet):
    if case == "0":
        return
    
    case = int(case)

    if correct:
        sheetDeclination["probability"][case-1] = 0.9 * sheetDeclination["probability"][case-1]
    else:
        sheetDeclination["probability"][case-1] = 1.1 * sheetDeclination["probability"][case-1]
    

    updateSheet(sheetDeclination,sheet)

tab1, tab2, tab3, tab4 = st.tabs(["Česky-Anglicky", "Anglicky-Česky", "Skloňování", "Přidat slovíčko"])


with tab1:

    if "sampleWord" not in st.session_state:
        st.session_state["sampleWord"] = sample(df)
    if "state" not in st.session_state:
        st.session_state["state"] = "new"
    if "example" not in st.session_state:
        st.session_state["example"] = ""
    


    if st.button("Nové slovíčko"):
        st.session_state["sampleWord"] = sample(df)
        st.session_state["state"] = "new"

    st.write(st.session_state["sampleWord"][0]["Czech"].values[0])
    gender = st.session_state["sampleWord"][0]["gender"].values[0]
    if gender != "":
        st.write(f"gender: {gender}")

    if st.button("Ukaž příklad"):
        example = getExample(st.session_state["sampleWord"][0]["Czech"].values[0])
        st.write(detectCase(st.session_state["sampleWord"][0]["Czech"].values[0],example))
        st.session_state["example"] = example
        st.session_state["state"] = "example"
    
    if st.session_state["state"] == "example" or st.session_state["state"] == "answer":
        st.write(st.session_state["example"])
        

        
    if st.button("Ukaž odpověd"):
        if st.session_state["state"] == "example":
            st.session_state["exampleTranslated"] = getTranslation(st.session_state["example"])
        else:
            st.session_state["exampleTranslated"] = ""
        st.session_state["state"] = "answer"
    
    if  st.session_state["state"] == "answer" or st.session_state["state"] == "feedback":
        st.write(st.session_state["sampleWord"][0]["English"].values[0])
        st.write(st.session_state["exampleTranslated"])

    if st.button("Dobře"):
        df["probability"].loc[st.session_state["sampleWord"][1]] = 0.9 * df["probability"].loc[st.session_state["sampleWord"][1]]
        updateSheet(df,worksheet)
        st.image("./happy.jpg",width=100)
        st.audio("./happy.mp3",autoplay=True)
        st.session_state["state"] = "feedback"

    if st.button("Špatně"):
        df["probability"].loc[st.session_state["sampleWord"][1]] = 1.1 * df["probability"].loc[st.session_state["sampleWord"][1]]
        updateSheet(df,worksheet)
        st.image("./unhappy.jpg",width=100)
        st.audio("./unhappy.mp3",autoplay=True)
        st.session_state["state"] = "feedback"
    

    
with tab2:
    if "sampleWord" not in st.session_state:
        st.session_state["sampleWord"] = sample(df)
    if "state2" not in st.session_state:
        st.session_state["state2"] = "new"
    if "example" not in st.session_state:
        st.session_state["example"] = ""
        st.session_state["exampleTranslated"] = ""
    


    if st.button("New word"):
        st.session_state["sampleWord"] = sample(df)
        st.session_state["state2"] = "new"

    st.write(st.session_state["sampleWord"][0]["English"].values[0])
        
    if st.button("Show answer"):
        st.session_state["exampleTranslated"] = ""
        st.session_state["state2"] = "answer"
        gender = st.session_state["sampleWord"][0]["gender"].values[0]
        if gender != "":
            st.write(f"gender: {gender}")
    
    if  st.session_state["state2"] == "answer" or st.session_state["state"] == "feedback":
        st.write(st.session_state["sampleWord"][0]["Czech"].values[0])
        

    if st.button("Correct"):
        df["probability"].loc[st.session_state["sampleWord"][1]] = 0.9 * df["probability"].loc[st.session_state["sampleWord"][1]]
        updateSheet(df,worksheet)
        st.image("./happy.jpg",width=100)
        st.audio("./happy.mp3",autoplay=True)
        st.session_state["state2"] = "feedback"

    if st.button("Wrong"):
        df["probability"].loc[st.session_state["sampleWord"][1]] = 1.1 * df["probability"].loc[st.session_state["sampleWord"][1]]
        updateSheet(df,worksheet)
        st.image("./unhappy.jpg",width=100)
        st.audio("./unhappy.mp3",autoplay=True)
        st.session_state["state2"] = "feedback"
    


    
       

with tab3:
    answer = ""
   

    def initSklonovani(df,df_declination):
        case = 15
        sampledCase = 32
        counter = 0
        while case != "0" and case != sampledCase:
            st.session_state["sampleWord"] = sample(df)
            czechWord = st.session_state["sampleWord"][0]["Czech"].values[0]
            sampledCase = int(sample(df_declination)[0]['case'].values[0])
            st.session_state["example"] = getExample(czechWord,case = sampledCase)
            
            case =  int(detectCase(czechWord,st.session_state["example"]))
            
            st.session_state['case'] = case
            options = getDeclination(st.session_state["sampleWord"][0]["Czech"].values[0],st.session_state["example"])
            optionsRandomised = randomiseOptions(options)
            st.session_state["sentence"] = blankWordOut(st.session_state["example"],st.session_state["sampleWord"][0]["Czech"].values[0])
            st.session_state["translation"] = getTranslation(st.session_state["example"],"cs-en")
            st.session_state["options"] = options
            st.session_state["optionsRandomised"] = np.append(optionsRandomised,"vyber možnost")
            st.session_state["state3"] = "new"
            st.session_state["explanation"] = explainDeclination(st.session_state["example"],st.session_state["sampleWord"][0]["Czech"].values[0])
            if case != 0 and case != sampledCase:
                if case == 0:
                    case = "NOT A NOUN"
                st.write(f"we've tried to generate a sentence using {sampledCase}th case of the word {czechWord} but it seems like the actual case is {case}")
                st.write(st.session_state["example"])
                st.write("trying again...")
            counter += 1
            if counter > 5:
                st.write("NEDARI SE VYGENEROVAT VĚTU")
                break
                

    if "sampleWord" not in st.session_state:
        st.session_state["sampleWord"] = sample(df)
    if "sentence" not in st.session_state:
        initSklonovani(df,df_declination)

    if st.button("Nová věta"):
        initSklonovani(df,df_declination)
    
    answer = st.radio(st.session_state["sentence"],st.session_state["optionsRandomised"],index=4)


    if answer == st.session_state["options"][0]:
        st.write("✅ Correct!")
        st.image("./happy.jpg",width=100)
        st.write(st.session_state["translation"])
        st.write(st.session_state["explanation"])
        updateCase(st.session_state['case'],True,df_declination,worksheetDeclination)        
        st.audio("./happy.mp3",autoplay=True)
    elif answer == "vyber možnost":
        pass
    else:
        st.write("❌ Try again.")
        st.image("./unhappy.jpg",width=100)
        st.write(st.session_state["translation"])  
        st.write(st.session_state["explanation"])
        updateCase(st.session_state['case'],False,df_declination,worksheetDeclination)
        st.audio("./unhappy.mp3",autoplay=True)



with tab4:
        
        czech = st.text_input("Česky")
        english = st.text_input("Anglicky")
        gender = st.text_input("rod m/f/n")
        if st.button("Přidat"):


            # New row as a DataFrame
            new_row = pd.DataFrame({'English': english, 'Type': "", 'Example': "", 'Czech': czech, 'probability': 1, 'gender': gender}, index=[0])

            # Append new row
            df = pd.concat([df, new_row], ignore_index=True)
       
            updateSheet(df,worksheet)
            st.write("Slovíčko bylo přidáno")
