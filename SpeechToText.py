import json
import os.path

from gtts import gTTS
from flask import Flask, request, send_from_directory
from gtts import gTTS
from flask_cors import CORS
from google.cloud import speech_v1p1beta1 as speech



app = Flask(__name__)
CORS(app)

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'key.json'

language_encode_dict = {"English (India)":"en-IN",
                        "English (United States)":"en-US",
                        "Hindi (India)":"hi-IN",
                        "Bengali (India)":"bn-IN",
                        "Finnish (Finland)":"fi-FI"}

@app.route('/t2s', methods=['GET', 'POST'])
def convertTextToSpeech():
    try:
        data = request.get_json()
        preferredName = data.get('preferredName')
        uid = data.get('uid')
        if not os.path.isdir(uid):
            os.makedirs(uid)
        language = 'en'
        myobj = gTTS(text=preferredName, lang=language, slow=False)
        myobj.save(uid + "\\preferredName.mp3")
        return send_from_directory(os.curdir + os.sep + uid, "preferredName.mp3", mimetype="audio/mpeg3",
                                   as_attachment=True)
    except:
        print("Something is wrong.")
    finally:
        print("finally entered")


@app.route('/s2t', methods=['POST'])
def speech_to_text():
    try:
        data = request.form['request']
        data = json.loads(data)
        print(data)
        uid = data.get('uid')
        country = data.get('country')
        if not os.path.isdir(uid):
            os.makedirs(uid)
        audio_file = request.files['audio']
        print(audio_file.filename)
        audio_file.save(uid + os.sep + audio_file.filename)

        with open(uid + os.sep + audio_file.filename, "rb") as f1:
            byte_data = f1.read()

        audio_mp3 = speech.RecognitionAudio(content=byte_data)
        client = speech.SpeechClient()
        config_mp3 = speech.RecognitionConfig(encoding=speech.RecognitionConfig.AudioEncoding.MP3,
                                              sample_rate_hertz=48000,
                                              language_code=language_encode_dict[country],
                                              audio_channel_count=2,
                                              model='latest_short',
                                              enable_separate_recognition_per_channel=False, )
        operation = client.long_running_recognize(config=config_mp3, audio=audio_mp3)
        print("Waiting for operation to complete...")
        response = operation.result(timeout=90)
        transcript = print_sentences(response)
        return transcript
    except Exception as e:
        print("Printing error")
        print(e)
        return e.message

@app.route('/t2s_v1', methods=['GET', 'POST'])
def synthesize_text():
    from google.cloud import texttospeech
    data = request.get_json()
    preferredName = data.get('preferredName')
    uid = data.get('uid')
    if not os.path.isdir(uid):
        os.makedirs(uid)

    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(text=preferredName)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Standard-C",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice, "audio_config": audio_config}
    )

    # The response's audio_content is binary.
    with open(uid + os.sep + "output.mp3", "wb") as out:
        out.write(response.audio_content)
        print('Audio content written to file "output.mp3"')
    return send_from_directory(os.curdir + os.sep + uid,"output.mp3", mimetype="audio/mpeg3",
                               as_attachment=True)


def print_sentences(response):
    print(response.results)
    print("inside transcript")
    for result in response.results:
        best_alternative = result.alternatives[0]
        transcript = best_alternative.transcript
        confidence = best_alternative.confidence
        print("-" * 80)
        print(f"Transcript: {transcript}")
        print(f"Confidence: {confidence:.0%}")
    return transcript;


if __name__ == '__main__':
    app.run(debug=True)
