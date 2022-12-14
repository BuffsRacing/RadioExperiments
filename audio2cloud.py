from sys import byteorder
from array import array
from struct import pack
from dotenv import load_dotenv

disable_azure = False

try:
    import azure.cognitiveservices.speech as speechsdk
except ModuleNotFoundError:
    print("Azure Speech SDK not installed. Please install it with pip install azure-cognitiveservices-speech")
    disable_azure = True
    
import os
import pyaudio
import time
import wave

THRESHOLD = 500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 44100

def is_silent(snd_data):
    "Returns 'True' if below the 'silent' threshold"
    return max(snd_data) < THRESHOLD

def normalize(snd_data):
    "Average the volume out"
    MAXIMUM = 16384
    times = float(MAXIMUM)/max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i*times))
    return r

def trim(snd_data):
    "Trim the blank spots at the start and end"
    def _trim(snd_data):
        snd_started = False
        r = array('h')

        for i in snd_data:
            if not snd_started and abs(i)>THRESHOLD:
                snd_started = True
                r.append(i)

            elif snd_started:
                r.append(i)
        return r

    # Trim to the left
    snd_data = _trim(snd_data)

    # Trim to the right
    snd_data.reverse()
    snd_data = _trim(snd_data)
    snd_data.reverse()
    return snd_data

def add_silence(snd_data, seconds):
    "Add silence to the start and end of 'snd_data' of length 'seconds' (float)"
    silence = [0] * int(seconds * RATE)
    r = array('h', silence)
    r.extend(snd_data)
    r.extend(silence)
    return r

def record(usb_audio_index):
    """
    Record a word or words from the microphone and 
    return the data as an array of signed shorts.

    Normalizes the audio, trims silence from the 
    start and end, and pads with 0.5 seconds of 
    blank sound to make sure VLC et al can play 
    it without getting chopped off.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE,
        input=True, output=True, input_device_index=usb_audio_index,
        frames_per_buffer=CHUNK_SIZE)

    num_silent = 0
    snd_started = False

    r = array('h')

    while 1:
        # little endian, signed short
        snd_data = array('h', stream.read(CHUNK_SIZE,exception_on_overflow = False)) # exception_on_overflow = False is because of some weird bug on macOS
        if byteorder == 'big':
            snd_data.byteswap()
        r.extend(snd_data)

        silent = is_silent(snd_data)

        if silent and snd_started:
            num_silent += 1
        elif not silent and not snd_started:
            snd_started = True

        if snd_started and num_silent > 30:
            break

    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()
    stream.close()
    p.terminate()

    r = normalize(r)
    r = trim(r)
    r = add_silence(r, 0.5)
    return sample_width, r

def record_to_file(path, usb_audio_index):
    "Records from the microphone and outputs the resulting data to 'path'"
    sample_width, data = record(usb_audio_index)
    data = pack('<' + ('h'*len(data)), *data)

    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()

def from_file(audio_fname, speech_key, speech_region):
    if disable_azure:
        return "Azure Speech SDK not installed."
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    audio_input = speechsdk.AudioConfig(filename=audio_fname)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

    result = speech_recognizer.recognize_once_async().get()
    print(f"Radio Transcript: {result.text}")
    return result.text

def natural_fname():
    return time.strftime("%Y%m%d_%H%M%S.wav", time.localtime())



if __name__ == '__main__':
    transcribe = True
    load_dotenv()
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")
    usb_audio_index = os.getenv("USB_AUDIO_INDEX")
    if speech_key is None or speech_region is None:
        print("Please set the AZURE_SPEECH_KEY and AZURE_SPEECH_REGION environment variables.")
        print("Disabling speech recognition.")
        transcribe = False
    if usb_audio_index is None:
        print("USB_AUDIO_INDEX enviornment variable not set.")
        print("Falling back to default (0)")
        usb_audio_index = 0
    try:
        usb_audio_index = int(usb_audio_index)
    except:
        print(f"Error converting {usb_audio_index} to int")
        usb_audio_index  = 0
    while True:
        print("Waiting for radio message...")
        audio_fname = f"BuffsRadio_{natural_fname()}"
        record_to_file(audio_fname, usb_audio_index)
        if transcribe:
            from_file(audio_fname,speech_key,speech_region)
        print("Recorded radio message.") 