import os
import base64
import streamlit as st
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig, ResultReason
from dotenv import load_dotenv
from openai import OpenAI
import streamlit.components.v1 as components


    # Load environment variables
load_dotenv()

def text_to_speech(text, language_code='hi-IN', voice_name='hi-IN-MadhurNeural'):
    speech_key = os.getenv('AZURE_SPEECH_KEY')
    service_region = os.getenv('AZURE_SPEECH_REGION')

    speech_config = SpeechConfig(subscription=speech_key, region=service_region)
    audio_config = AudioConfig(filename="response.mp3")
    speech_config.speech_synthesis_voice_name = voice_name
    synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    
    result = synthesizer.speak_text_async(text).get()
    if result.reason != ResultReason.SynthesizingAudioCompleted:
        print(f"Speech synthesis canceled: {result.cancellation_details.reason}")
        return None

    return "response.mp3"

# Set up OpenAI API
client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY")
)


def generate_response(prompt, language):
    language_instruction = f"User choice is '{language}'."
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You have choices: 1. English 2. Hindi and 3. Japanees. If the user's choice is 'Hindi', then translate the input to Hindi. If the user's choice is 'English', then keep the input as is and do not add anything with user input just keep as it is. and if user choose japanees then convert into japanees."},
            {"role": "user", "content": f"{language_instruction} {prompt}"}
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content

def get_base64_audio(audio_file):
    with open(audio_file, "rb") as f:
        audio_bytes = f.read()
    return base64.b64encode(audio_bytes).decode()

# Streamlit app
st.title("Text-to-Speech Bot")


# Language selection
language = st.radio("Choose language", ('English', 'Hindi', 'Japanees'))

# Available voices
voices = {
    'English': ['en-US-JennyNeural', 'en-US-GuyNeural', 'en-AU-NatashaNeural'],
    'Hindi': ['hi-IN-MadhurNeural', 'hi-IN-SwaraNeural', 'hi-IN-MohanNeural'],
    'Japanees': ['ja-JP-KeitaNeural', 'ja-JP-AoiNeural', 'ja-JP-MayuNeural']
}

if language == 'Hindi':
    language_code = 'hi-IN'
elif language == 'Japanees':
    language_code = 'ja-JP'
else:
    language_code = 'en-US'

# Voice selection
voice_name = st.selectbox("Choose voice", voices[language])

# Text input
user_input = st.text_area("Enter your text:")

# Process input
if st.button("Generate Speech"):
    if user_input:
        with st.spinner("Generating response..."):
            response_text = generate_response(user_input, language)
            st.write("Generated Response:")
            st.write(response_text)
            audio_file = text_to_speech(response_text, language_code, voice_name)
            if audio_file:
                # Encode audio to base64
                audio_base64 = get_base64_audio(audio_file)
                
                # HTML and JavaScript for real-time waveform visualization
                components.html(f"""
                <html>
                <head>
                    <script src="https://unpkg.com/wavesurfer.js"></script>
                    <style>
                        .audio-container {{
                            width: 100%;
                            max-width: 800px;
                            margin: 0 auto;
                        }}
                        audio {{
                            width: 100%;
                        }}
                        #waveform {{
                            width: 100%;
                            margin-top: 20px;
                        }}
                        .download-button {{
                            display: inline-block;
                            margin-top: 10px;
                            padding: 10px 20px;
                            background-color: #007bff;
                            color: white;
                            text-decoration: none;
                            border-radius: 5px;
                            text-align: center;
                        }}
                    </style>
                </head>
                <body>
                    <div class="audio-container">
                        <audio id="audio" controls>
                            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                        </audio>
                        <div id="waveform"></div>
                        <a id="download-link" href="data:audio/mp3;base64,{audio_base64}" download="response.mp3" class="download-button">Download Audio</a>
                    </div>
                    <script>
                        document.addEventListener('DOMContentLoaded', function() {{
                            var wavesurfer = WaveSurfer.create({{
                                container: '#waveform',
                                waveColor: 'white',
                                progressColor: 'green'
                            }});
                            
                            var audioElement = document.getElementById('audio');
                            audioElement.addEventListener('play', function() {{
                                wavesurfer.play();
                            }});
                            audioElement.addEventListener('pause', function() {{
                                wavesurfer.pause();
                            }});
                            audioElement.addEventListener('seeked', function() {{
                                wavesurfer.seekTo(audioElement.currentTime / audioElement.duration);
                            }});
                            
                            wavesurfer.load('data:audio/mp3;base64,{audio_base64}');
                        }});
                    </script>
                </body>
                </html>
                """, height=300)
                os.remove(audio_file)
            else:
                st.error("Failed to generate speech.")
    else:
        st.warning("Please enter some text.")