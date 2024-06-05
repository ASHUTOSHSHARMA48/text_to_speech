import os
import streamlit as st
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig, ResultReason
from dotenv import load_dotenv
from openai import OpenAI

    # Load environment variables
load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

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
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def generate_response(prompt, language):
    language_instruction = f"User choice is '{language}'."
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You have two choices: 1. English and 2. Hindi. If the user's choice is 'Hindi', then translate the input to Hindi. If the user's choice is 'English', then keep the input as is."},
            {"role": "user", "content": f"{language_instruction} {prompt}"}
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content

# Streamlit app
st.title("Text-to-Speech Bot")

# Language selection
language = st.radio("Choose language", ('English', 'Hindi'))
if language == 'Hindi':
    language_code = 'hi-IN'
    voice_name = 'hi-IN-MadhurNeural'
else:
    language_code = 'en-US'
    voice_name = 'en-US-JennyNeural'

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
                audio_bytes = open(audio_file, 'rb').read()
                st.audio(audio_bytes, format='audio/mp3')
                os.remove(audio_file)
            else:
                st.error("Failed to generate speech.")
    else:
        st.warning("Please enter some text.")