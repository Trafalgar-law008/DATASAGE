import os
import logging
import tempfile
import pandas as pd
import google.generativeai as genai
import telebot
from gtts import gTTS

logging.basicConfig(level=logging.DEBUG)

genai.configure(api_key="YOUR_GEMINI_API_KEY_HERE")
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

bot = telebot.TeleBot(BOT_TOKEN)
model = genai.GenerativeModel("models/gemini-1.5-flash-002")

def load_csv_from_file(file_path):
    """Load CSV file into a DataFrame."""
    return pd.read_csv(file_path)

def perform_eda(data):
    """Perform Exploratory Data Analysis (EDA) using Gemini AI."""
    summary = data.describe(include="all").to_json()
    eda_prompt = f"Perform exploratory data analysis on this dataset: {summary}"
    response = model.generate_content(eda_prompt)
    logging.debug(f"EDA Response: {response.text}")
    return response.text

def generate_insights(eda_result):
    """Generate insights based on EDA results."""
    insight_prompt = f"Generate insights based on this EDA: {eda_result}"
    response = model.generate_content(insight_prompt)
    logging.debug(f"Insights Response: {response.text}")
    return response.text

def create_podcast_script(insights):
    """Create a natural, engaging conversation based on insights."""
    script_prompt = f"""
    Create a natural conversation between Alex and Sarah discussing these data insights.
    Make it sound casual and engaging.
    Insights: {insights}
    """
    response = model.generate_content(script_prompt)
    logging.debug(f"Podcast Script Response: {response.text}")
    return response.text

def generate_audio(script, filename="podcast.mp3"):
    """Generate audio using gTTS."""
    tts = gTTS(script, lang="en")
    tts.save(filename)
    return filename

@bot.message_handler(commands=["start"])
def send_welcome(message):
    """Handle the /start command."""
    welcome_text = """
    Welcome to the Data Analysis Podcast Bot! 📊🎙
    Send me a CSV file, and I'll analyze it and create a podcast for you.
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=["help"])
def send_help(message):
    """Handle the /help command."""
    help_text = """
    Available commands:
    /start - Start the bot
    /help - Show this help message
    To analyze data:
    1. Send a CSV file
    2. Wait for the analysis
    3. Receive your audio podcast!
    """
    bot.reply_to(message, help_text)

@bot.message_handler(content_types=["document"])
def handle_csv(message):
    """Handle CSV file uploads."""
    try:
        if not message.document.file_name.endswith(".csv"):
            bot.reply_to(message, "Please send a CSV file only.")
            return
        
        bot.reply_to(message, "Receiving your CSV file... 📥")
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            temp_file.write(downloaded_file)
            file_path = temp_file.name

        bot.reply_to(message, "Analyzing your data... 🔍")
        data = load_csv_from_file(file_path)

        bot.reply_to(message, "Generating EDA results... 📊")
        eda_result = perform_eda(data)

        bot.reply_to(message, "Generating insights... 💡")
        insights = generate_insights(eda_result)

        bot.reply_to(message, "Creating podcast script... ✍")
        podcast_script = create_podcast_script(insights)

        bot.reply_to(message, "Generating audio... 🎙")
        audio_path = generate_audio(podcast_script)

        with open(audio_path, "rb") as audio_file:
            bot.send_audio(message.chat.id, audio_file, caption="Here's your data analysis podcast! 🎧")

        os.unlink(file_path)
        os.unlink(audio_path)
    except Exception as e:
        logging.error(f"Error processing file: {e}")
        bot.reply_to(message, f"Sorry, an error occurred: {str(e)}")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    """Handle all other messages."""
    bot.reply_to(message, "Please send a CSV file to analyze, or use /help to see available commands.")

if __name__ == "__main__":
    bot.infinity_polling()
