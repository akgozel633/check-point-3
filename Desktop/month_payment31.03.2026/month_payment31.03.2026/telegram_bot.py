#!/usr/bin/env python3
"""
Clean Telegram Payment Bot - Fresh Start
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import re

# Your bot token from @BotFather
BOT_TOKEN = "8793242576:AAFHK7xffHGC8dslqWODNq3xcTkemzy84Ow"
WEBAPP_URL = "http://127.0.0.1:5000"

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "🪙 Welcome to Payment Bot!\n\n"
        "Send payment in format: PAY [amount] [email]\n"
        "• PAY 5 your@email.com - Add 5 tokens\n"
        "• PAY 10.5 your@email.com - Add 10.5 tokens\n\n"
        "Example: PAY 5 john@example.com\n\n"
        "Use the same email you registered with!"
    )

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment messages"""
    message_text = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    
    # Extract amount and email from message
    match = re.search(r'PAY\s+(\d+(?:\.\d+)?)\s+([^\s]+)', message_text, re.IGNORECASE)
    if not match:
        await update.message.reply_text(
            "❌ Invalid format. Use: PAY [amount] [email]\n"
            "Example: PAY 5 john@example.com"
        )
        return
    
    amount = float(match.group(1))
    email = match.group(2).lower()
    
    # Send payment to your Flask app
    payment_data = {
        'telegram_id': user_id,
        'username': email,  # Send email for lookup
        'amount': amount,
        'message': message_text
    }
    
    try:
        await update.message.reply_text(f"🔄 Processing payment of {amount} tokens...")
        
        response = requests.post(
            f"{WEBAPP_URL}/api/payment/telegram",
            json=payment_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            await update.message.reply_text(
                f"✅ Payment successful!\n\n"
                f"Amount: {result.get('amount', amount)} tokens\n"
                f"New Balance: {result.get('new_balance', 'Unknown')} tokens\n"
                f"Transaction ID: {result.get('payment_id', 'Unknown')}"
            )
        else:
            error_msg = response.json().get('error', 'Unknown error')
            await update.message.reply_text(f"❌ Payment failed: {error_msg}")
            
    except requests.exceptions.Timeout:
        await update.message.reply_text(
            "❌ Payment processing timed out.\n"
            "Please try again in a moment."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    """Start the bot"""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_payment))
        
        print("🤖 Telegram Payment Bot Started!")
        print("Connected to Telegram successfully!")
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")
        print("\n🔧 Solutions:")
        print("1. Use a VPN to connect to Turkey/Russia, then run bot")
        print("2. Deploy bot to a server outside Turkmenistan")
        print("3. Use web interface: http://localhost:5000/test-payment")

if __name__ == '__main__':
    main()
