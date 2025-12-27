import os
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests
import logging

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Get tokens
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY")

if not TOKEN or not DEEPSEEK_KEY:
    print("ERROR: Missing API keys!")
    print(f"Telegram Token: {'Set' if TOKEN else 'Missing'}")
    print(f"DeepSeek Key: {'Set' if DEEPSEEK_KEY else 'Missing'}")
    sys.exit(1)

async def start(update: Update, context):
    await update.message.reply_text("✅ Bot is working! Send me a topic for an essay.")

async def help(update: Update, context):
    await update.message.reply_text("Send me any topic and I'll write an essay about it!")

async def handle_message(update: Update, context):
    topic = update.message.text
    
    # Tell user we're working on it
    msg = await update.message.reply_text(f"📝 Writing essay about: {topic}...")
    
    try:
        # Call DeepSeek API
        headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": f"Write a 500-word essay about: {topic}"}],
            "max_tokens": 1000
        }
        
        response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        essay = response.json()['choices'][0]['message']['content']
        
        # Send in chunks if too long
        if len(essay) > 4000:
            for i in range(0, len(essay), 4000):
                await update.message.reply_text(essay[i:i+4000])
        else:
            await update.message.reply_text(f"📄 **Essay:**\n\n{essay}")
            
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
        
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ Error generating essay. Please try again.")

def main():
    print("🚀 Starting bot...")
    print(f"Using Telegram token: {TOKEN[:10]}...")
    print(f"Using DeepSeek key: {DEEPSEEK_KEY[:10]}...")
    
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
