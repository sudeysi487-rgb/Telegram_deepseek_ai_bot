import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests
import asyncio

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get tokens from environment
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY")

if not TOKEN or not DEEPSEEK_KEY:
    logger.error("Missing API tokens!")
    logger.error(f"Telegram Token: {'SET' if TOKEN else 'MISSING'}")
    logger.error(f"DeepSeek Key: {'SET' if DEEPSEEK_KEY else 'MISSING'}")
    exit(1)

async def start(update: Update, context):
    """Handle /start command"""
    await update.message.reply_text(
        "🤖 **AI Essay Writer Bot**\n\n"
        "I can write essays on any topic using AI!\n"
        "Just send me a topic and I'll write an essay for you.\n\n"
        "Example: 'Climate change' or 'Benefits of reading'"
    )

async def help_command(update: Update, context):
    """Handle /help command"""
    await update.message.reply_text(
        "📚 **Help Guide**\n\n"
        "Just send me any topic and I'll write an essay!\n\n"
        "**Commands:**\n"
        "/start - Start the bot\n"
        "/help - Show this message\n\n"
        "**Example topics:**\n"
        "• Artificial intelligence\n"
        "• Importance of education\n"
        "• Renewable energy\n"
        "• Mental health awareness"
    )

async def handle_message(update: Update, context):
    """Handle any text message"""
    topic = update.message.text
    
    # Show typing action
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    
    # Send processing message
    status_msg = await update.message.reply_text(
        f"📝 **Writing essay about:**\n_{topic}_\n\n⏳ Please wait..."
    )
    
    try:
        # Prepare API request
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Write a comprehensive, well-structured essay on the topic: "{topic}"

Requirements:
1. Include introduction, body paragraphs, and conclusion
2. Use academic but accessible language
3. Include relevant examples
4. Keep it between 300-500 words
5. Make it sound natural and human-written"""

        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are an expert academic writer."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.7
        }
        
        # Call DeepSeek API
        logger.info(f"Generating essay for topic: {topic}")
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        
        essay = result['choices'][0]['message']['content']
        logger.info(f"Essay generated successfully ({len(essay)} characters)")
        
        # Delete processing message
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id
        )
        
        # Send essay (split if too long)
        if len(essay) > 4000:
            # Split into chunks
            chunks = [essay[i:i+4000] for i in range(0, len(essay), 4000)]
            for i, chunk in enumerate(chunks, 1):
                prefix = f"📄 **Essay (Part {i}/{len(chunks)}):**\n\n" if len(chunks) > 1 else "📄 **Essay:**\n\n"
                await update.message.reply_text(prefix + chunk)
        else:
            await update.message.reply_text(f"📄 **Essay:**\n\n{essay}")
        
        # Send completion message
        await update.message.reply_text(
            "✅ **Essay completed!**\n\n"
            "Send another topic or /help for assistance."
        )
        
    except requests.exceptions.Timeout:
        await update.message.reply_text("❌ Request timed out. Please try again.")
        logger.error("DeepSeek API timeout")
    except requests.exceptions.RequestException as e:
        await update.message.reply_text("❌ Error connecting to AI service. Please try again later.")
        logger.error(f"API request error: {e}")
    except Exception as e:
        await update.message.reply_text("❌ An unexpected error occurred. Please try again.")
        logger.error(f"Unexpected error: {e}")

def main():
    """Start the bot"""
    logger.info("Starting Telegram AI Essay Bot...")
    logger.info(f"Bot token: {TOKEN[:15]}...")
    logger.info(f"DeepSeek key: {DEEPSEEK_KEY[:15]}...")
    
    try:
        # Create application
        application = Application.builder().token(TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Start bot
        logger.info("Bot is now running...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        exit(1)

if __name__ == "__main__":
    main()
