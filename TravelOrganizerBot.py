#Telegram BOT
#An application of our AI Agents To search Travel information
#like flight, weather & itinerary info

#imports library
import threading
import time
from datetime import datetime
import re
import os
import schedule
from pydub import AudioSegment
import speech_recognition as sr
from telebot import TeleBot
from datetime import date

from TravelOrganizerLLM import askLLMPriority
from TravelOrganizerLLM import askLLM

print(">> LLM caricata")
BOT_TOKEN = "bot token"

#Bot Instance
bot = TeleBot(BOT_TOKEN)

# Schedulatore globale
scheduler = schedule

# /start message handler from users
@bot.message_handler(commands=['start'])
def send_description(message):
    idT = message.chat.id

    res = f"""_Ciao, mi chiamo_ ✈️🧳 *FlyNow*\n_Sono un AI agente di viaggi. Ti aiuterò ad organizzare i tuoi prossimi viaggi._
    \n\n_Dimmi dove vorresti andare e da dove parti e il periodo e farò le migliori ricerche per te\n
    \n(Es. Cerca voli andata e ritorno da Roma per Madrid dal 20 al 25 Novembre)_"""
    bot.delete_message(idT, message.id)
    sendMessage(idT, res)


# Function that handles text messages
def sendMessage(idT, message):
    idM = ""
    try:
        idM = bot.send_message(idT,message,"markdown")
    except Exception as e:
        print(e)
        t = message.replace("#","").replace("_","")
        try:
            idM = bot.send_message(idT,message,"markdown")
        except:
            idM = bot.send_message(idT,message)
    return idM

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    idT = message.chat.id
    t = message.text
    print(f"Mess ricevuto:\n\"{t}\"\n\n")
    idM = sendMessage(idT, "Sto esaminando le tue richieste...")
    print("\nTyping\n")
    bot.send_chat_action(idT, "typing")
    ask = f"{t}.\nTogli i doppi asterischi nel testo che mi hai dato come risultato e formattalo attraverso il markdown di messaggi telegram mettendo frasi o parole tra * o tra _ e per dare più enfasi aggiungi qualche emoji"
    res = f"{askLLM(ask)}"
    sendMessage(idT, res)
    bot.delete_message(idT,idM.id)
    print("END hendler mess")



# Riconoscitore vocale globale
recognizer = sr.Recognizer()

# Function to manage voice messages
@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    idT = message.chat.id
    file_info = bot.get_file(message.voice.file_id)
    ogg_path = "voice_message.ogg"
    wav_path = "voice_message.wav"

    # Scarica il file vocale dal server di Telegram
    downloaded_file = bot.download_file(file_info.file_path)
    with open(ogg_path, 'wb') as f:
        f.write(downloaded_file)

    # Converti il file .ogg in .wav
    audio = AudioSegment.from_ogg(ogg_path)
    audio.export(wav_path, format="wav")

    # Trascrivi l'audio
    print("Audio ricevuto...")
    idM = sendMessage(idT, "Sto esaminando le tue richieste...")
    print("\nTyping\n")
    bot.send_chat_action(idT, "typing")
    testo = trascrivi_audios(wav_path)

    ask = f"{testo}.\nTogli i doppi asterischi nel testo che mi hai dato come risultato e formattalo attraverso il markdown di messaggi telegram mettendo frasi o parole tra * o tra _ e per dare più enfasi aggiungi qualche emoji"
    #t = response(t, idT)
    res = f"{askLLM(ask)}"
    #t = f"Formatta il seguente testo per il markdown di telegram:\n\n{askLLM(t)}"
    sendMessage(idT, res)
    bot.delete_message(idT,idM.id)

    print(testo)
    #resp = response(testo, idT)
    #bot.reply_to(message, f"{res}")
    os.remove(ogg_path)
    os.remove(wav_path)

# Function to transcribe audio
def trascrivi_audios(file_path):
    print("Rilevo traccia...")
    try:
        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(source)
            testo = recognizer.recognize_google(audio, language='it-IT')
            print("Testo rilevato...")
            return testo
    except sr.UnknownValueError:
        return "Non ho capito l'audio."
    except sr.RequestError as e:
        return f"Errore di riconoscimento vocale: {e}"

# Function to start polling the bot
def polling_thread():
    bot.infinity_polling()

# Start bot polling in a separate thread
polling_thread = threading.Thread(target=polling_thread)
polling_thread.start()

# Keeps the scheduler running
while True:
    scheduler.run_pending()
    time.sleep(1)