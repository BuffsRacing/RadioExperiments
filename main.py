import random
import re
import sys
from flask import Flask, render_template
from turbo_flask import Turbo
import threading
import time
import os
from datetime import datetime, date

from audio2cloud import *

import pickle

load_dotenv()
speech_key = os.getenv("AZURE_SPEECH_KEY")
speech_region = os.getenv("AZURE_SPEECH_REGION")
usb_audio_index = os.getenv("USB_AUDIO_INDEX")
transcribe = os.getenv("ENABLE_TRANSCRIPTION")
try:
    transcribe = bool(transcribe)
except:
    transcribe = False
record_messages = os.getenv("ENABLE_RECORDING")
try:
    record_messages = bool(record_messages)
except:
    record_messages = False

app = Flask(__name__)
app.config["SERVER_NAME"] = "localhost:5000"
app.config['TEMPLATES_AUTO_RELOAD'] = True
turbo = Turbo(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.context_processor
def inject_messages():
    fnames = os.listdir("static/")
    todays_files = []
    with open("transcripts.pkl", "rb") as f:
        transcriptions = pickle.load(f)
        f.close()
    for fname in fnames:
        if "BuffsRadio" not in fname:
            continue
        dt_obj = datetime.strptime(fname, 'BuffsRadio_%Y%m%d_%H%M%S.wav')
        message = "Transcription not available..."
        if f"static/{fname}" in transcriptions:
            message = transcriptions[f"static/{fname}"]
        if dt_obj.date() == date.today():
            todays_files.append(
                {
                    "file": fname,
                    "dt_obj": dt_obj.isoformat(),
                    "transcript": message
                }
            )
        if todays_files != []:
            todays_files = sorted(todays_files, key=lambda k: k['dt_obj'], reverse=True) # Sort by date
    return {'todays_files': todays_files}


def update_messages():
    with app.app_context():
        while True:
            audio_fname = f"static/BuffsRadio_{natural_fname()}"
            if record_messages:
                print("ready to record message...")
                record_to_file(audio_fname, usb_audio_index)
                print("done recording message...")
            with open("transcripts.pkl", "rb") as f:
                transcriptions = pickle.load(f)
                f.close()
            if transcriptions is None:
                transcriptions = {}
            if transcribe:
                print("processing message...")
                transcriptions[audio_fname]=from_file(audio_fname,speech_key,speech_region)
            with open("transcripts.pkl", "wb") as f:
                pickle.dump(transcriptions, f)
                f.close()
            turbo.push(turbo.replace(render_template('radioMessages.html'), 'todays_files'))
            time.sleep(10000)

@app.before_first_request
def before_first_request():
    threading.Thread(target=update_messages).start()

if __name__ == '__main__':
    app.run(debug=True)