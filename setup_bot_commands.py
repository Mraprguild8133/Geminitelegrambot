import asyncio
from telegram import Bot, BotCommand
from config import config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_bot_commands():
    """Setup bot commands automatically via Telegram API"""
    bot = Bot(token=config.BOT_TOKEN)
    
    # Define all bot commands
    commands = [
        BotCommand("start", "🚀 Start the bot and see welcome message"),
        BotCommand("help", "🆘 Show all available commands and features"),
        BotCommand("admin", "👑 Access admin control panel"),
        BotCommand("ban", "🚫 Ban a user (Admin only)"),
        BotCommand("unban", "✅ Unban a user (Admin only)"),
        BotCommand("addadmin", "👑 Add new admin (Owner only)"),
        BotCommand("deladmin", "❌ Remove admin (Owner only)"),
        BotCommand("scan", "🔍 Manually scan URL for security threats"),
        BotCommand("contact", "📞 Get developer contact and support information"),
    ]
    
    try:
        # Set commands for the bot
        await bot.set_my_commands(commands)
        logger.info("✅ Bot commands set successfully!")
        
        # Set bot description
        await bot.set_my_description(
            f"🤖 Advanced Telegram Bot by {config.BOT_OWNER_NAME}\n\n"
            "🔥 Features:\n"
            "• AI Assistant powered by Gemini\n"
            "• File Management & Storage\n" 
            "• Content Moderation & Security\n"
            "• Automatic URL Scanning\n"
            "• Admin Management Tools\n"
            "• Bad Word Filtering\n\n"
            "Ready to assist you! 🚀"
        )
        logger.info("✅ Bot description set successfully!")
        
        # Set bot short description
        await bot.set_my_short_description(
            f"🤖 Advanced Bot by {config.BOT_OWNER_NAME} - AI Assistant, File Management, Security & More!"
        )
        logger.info("✅ Bot short description set successfully!")
        
        # Get bot info to verify
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot setup complete for: @{bot_info.username}")
        
        print("🎉 Bot commands setup completed successfully!")
        print("\n📋 Commands registered:")
        for cmd in commands:
            print(f"/{cmd.command} - {cmd.description}")
            
        print(f"\n🤖 Bot: @{bot_info.username}")
        print(f"👑 Owner: {config.BOT_OWNER_NAME}")
        print("✅ All automatic setup completed!")
        
    except Exception as e:
        logger.error(f"❌ Error setting up bot commands: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(setup_bot_commands())