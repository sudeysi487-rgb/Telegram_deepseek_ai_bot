import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)

# Get environment variables
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY")

print(f"Starting bot with token: {TOKEN[:10]}...")

async def start(update: Update, context):
    await update.message.reply_text("🤖 AI Essay Bot Ready!\nSend me a topic to write an essay about.")

async def handle_message(update: Update, context):
    topic = update.message.text
    await update.message.reply_text(f"📝 Writing essay about: {topic}...")
    
    try:
        # Call DeepSeek API
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are an expert essay writer."},
                {"role": "user", "content": f"Write a detailed essay about: {topic}"}
            ],
            "max_tokens": 1000
        }
        
        response = requests.post("https://api.deepseek.com/v1/chat/completions", 
                                headers=headers, json=data, timeout=30)
        
        essay = response.json()['choices'][0]['message']['content']
        
        # Send essay
        await update.message.reply_text(f"📄 **Essay:**\n\n{essay}")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ Error. Please try again.")

def main():
    # Create bot application
    app = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start polling
    print("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
