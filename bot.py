import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes
)

from config import config
from gemini_ai import GeminiAI
from content_moderation import ContentModerator
from file_manager import FileManager
from url_scanner import URLScanner
from user_manager import UserManager

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        """Initialize the bot with all components"""
        self.application = Application.builder().token(config.BOT_TOKEN).build()
        self.bot = self.application.bot
        
        # Initialize components
        self.gemini_ai = GeminiAI()
        self.content_moderator = ContentModerator()
        self.file_manager = FileManager(self.bot)
        self.url_scanner = URLScanner()
        self.user_manager = UserManager(self.bot)
        
        self.setup_handlers()

    def setup_handlers(self):
        """Setup all command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        self.application.add_handler(CommandHandler("ban", self.ban_command))
        self.application.add_handler(CommandHandler("unban", self.unban_command))
        self.application.add_handler(CommandHandler("addadmin", self.add_admin_command))
        self.application.add_handler(CommandHandler("deladmin", self.del_admin_command))
        self.application.add_handler(CommandHandler("scan", self.scan_url_command))
        self.application.add_handler(CommandHandler("contact", self.contact_command))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        
        # Callback handlers
        from telegram.ext import CallbackQueryHandler
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_text = f"""
🤖 **Welcome to {config.BOT_OWNER_NAME}'s Advanced Bot!**

🔥 **Features:**
• 🤖 AI Assistant powered by Gemini
• 📁 File Management (All formats supported)
• 🛡️ Content Moderation & Copyright Protection
• 🔗 URL Scanner for security
• 👥 Advanced Admin Tools
• 🚫 Automatic Bad Word Filtering

**Commands:**
/help - Show all commands
/admin - Admin panel
/scan <url> - Scan URL for safety

**Developer Contact:**
📱 Telegram: @Sathishkumar33
📧 Email: Mraprguild@gmail.com
🆘 Support: Available for help & queries

Ready to assist you! 🚀
        """
        
        await update.message.reply_text(welcome_text)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🆘 **Bot Commands & Features**

**🤖 AI Assistant:**
• Just send any text message for AI response

**📁 File Management:**
• Send any file to store it safely

**👑 Admin Commands:**
• `/ban <user_id>` - Ban a user
• `/unban <user_id>` - Unban a user  
• `/addadmin <user_id>` - Add admin (Owner only)
• `/deladmin <user_id>` - Remove admin (Owner only)

**🔒 Security Features:**
• `/scan <url>` - Scan URL for threats
• Automatic content moderation

**📞 Developer & Support:**
📱 **Developer:** @Sathishkumar33
📧 **Email:** Mraprguild@gmail.com
🆘 **Support:** Contact for help, issues, or feature requests
💬 **Updates:** Follow for bot updates and announcements

Made with ❤️ by {config.BOT_OWNER_NAME}
        """
        
        await update.message.reply_text(help_text)

    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        user_id = update.effective_user.id
        
        if not await self.user_manager.is_admin(user_id):
            await update.message.reply_text("❌ You don't have admin permissions!")
            return
        
        keyboard = [
            [InlineKeyboardButton("📊 Bot Statistics", callback_data="admin_stats")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("👑 **Admin Panel**", reply_markup=reply_markup)

    async def ban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ban command"""
        if not await self.user_manager.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have admin permissions!")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/ban <user_id>`")
            return
        
        try:
            user_id = int(context.args[0])
            success = await self.user_manager.ban_user(
                user_id, update.effective_chat.id, update.effective_user.id
            )
            
            if success:
                await update.message.reply_text(f"✅ User {user_id} has been banned!")
            else:
                await update.message.reply_text("❌ Failed to ban user!")
                
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")

    async def unban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unban command"""
        if not await self.user_manager.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have admin permissions!")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/unban <user_id>`")
            return
        
        try:
            user_id = int(context.args[0])
            success = await self.user_manager.unban_user(
                user_id, update.effective_chat.id, update.effective_user.id
            )
            
            if success:
                await update.message.reply_text(f"✅ User {user_id} has been unbanned!")
            else:
                await update.message.reply_text("❌ Failed to unban user!")
                
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")

    async def add_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /addadmin command"""
        if not await self.user_manager.is_owner(update.effective_user.id):
            await update.message.reply_text("❌ Only the owner can add admins!")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/addadmin <user_id>`")
            return
        
        try:
            user_id = int(context.args[0])
            success = await self.user_manager.add_admin(user_id, update.effective_user.id)
            
            if success:
                await update.message.reply_text(f"✅ User {user_id} is now an admin!")
            else:
                await update.message.reply_text("❌ Failed to add admin!")
                
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")

    async def del_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /deladmin command"""
        if not await self.user_manager.is_owner(update.effective_user.id):
            await update.message.reply_text("❌ Only the owner can remove admins!")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/deladmin <user_id>`")
            return
        
        try:
            user_id = int(context.args[0])
            success = await self.user_manager.remove_admin(user_id, update.effective_user.id)
            
            if success:
                await update.message.reply_text(f"✅ Admin privileges removed from user {user_id}!")
            else:
                await update.message.reply_text("❌ Failed to remove admin!")
                
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")

    async def scan_url_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /scan command"""
        if not context.args:
            await update.message.reply_text("Usage: `/scan <url>`")
            return
        
        url = context.args[0]
        await update.message.reply_text("🔍 Scanning URL... Please wait.")
        
        result = await self.url_scanner.scan_url(url)
        
        response = f"🔍 **URL Scan Results**\n\n" \
                  f"**URL:** `{url}`\n" \
                  f"**Status:** {result['message']}\n" \
                  f"**Risk Level:** {result['risk_level'].upper()}"
        
        await update.message.reply_text(response, disable_web_page_preview=True)

    async def contact_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /contact command"""
        contact_text = f"""
📞 **Developer & Support Contact**

👨‍💻 **Developer:** {config.BOT_OWNER_NAME}
📱 **Telegram:** @Sathishkumar33
📧 **Email:** Mraprguild@gmail.com

🆘 **Support Available For:**
• Bot issues & troubleshooting
• Feature requests & suggestions  
• Technical support & questions
• Custom modifications & updates

💬 **Response Time:** Usually within 24 hours
🤝 **Professional Support:** Available for all users

Feel free to reach out anytime for assistance!
        """
        
        await update.message.reply_text(contact_text)

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        text = update.message.text
        
        if not text:
            return
            
        user_id = update.effective_user.id
        
        # Check for URLs in message and scan automatically
        urls = self.url_scanner.extract_urls_from_text(text)
        if urls:
            # Send scanning notification
            scan_msg = await update.message.reply_text("🔍 Automatically scanning URLs for security...")
            
            # Scan URLs and take action
            urls_blocked = await self.handle_urls_in_message(update, urls)
            
            if urls_blocked:
                # If URLs were blocked, don't process the message further
                await scan_msg.delete()
                return
            else:
                # URLs are safe, update the scan message
                await scan_msg.edit_text("✅ URLs scanned - all safe!")
        
        # Content moderation
        moderation_result = await self.content_moderator.check_text_content(text)
        
        if not moderation_result["is_safe"]:
            # Delete message and warn user
            try:
                await update.message.delete()
                warning_text = f"⚠️ Message removed due to: {', '.join(moderation_result['violations'])}"
                await update.message.reply_text(warning_text)
            except:
                pass
            return
        
        # Generate AI response
        await update.message.reply_text("🤖 Thinking...")
        
        try:
            ai_response = await self.gemini_ai.generate_response(text)
            await update.message.reply_text(ai_response)
        except Exception as e:
            await update.message.reply_text("Sorry, I encountered an error processing your request.")

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads"""
        await self.process_file_upload(update, context, update.message.document)

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo uploads"""
        photo = update.message.photo[-1]
        await self.process_file_upload(update, context, photo)

    async def process_file_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_obj):
        """Process file upload"""
        try:
            await update.message.reply_text("📁 Processing your file...")
            
            file = await context.bot.get_file(file_obj.file_id)
            filename = getattr(file_obj, 'file_name', f"file_{file_obj.file_id}")
            if not filename:
                filename = f"file_{file_obj.file_id}.unknown"
            
            file_path = os.path.join("uploads", filename)
            os.makedirs("uploads", exist_ok=True)
            
            await file.download_to_drive(file_path)
            
            result = await self.file_manager.save_user_file(
                file_path, update.effective_user.id, filename
            )
            
            if result["success"]:
                response = f"✅ **File Saved Successfully!**\n\n" \
                          f"📁 **Filename:** `{filename}`\n" \
                          f"🆔 **File ID:** `{result['message_id']}`"
                await update.message.reply_text(response)
            else:
                await update.message.reply_text("❌ Failed to save file.")
            
            # Cleanup
            if os.path.exists(file_path):
                os.remove(file_path)
            
        except Exception as e:
            logger.error(f"File upload error: {e}")
            await update.message.reply_text("❌ Error processing file. Please try again.")

    async def handle_urls_in_message(self, update: Update, urls: list) -> bool:
        """Handle URLs found in messages - returns True if URLs were blocked"""
        for url in urls:
            result = await self.url_scanner.scan_url(url)
            
            if not result["is_safe"] and result["risk_level"] in ["high", "medium"]:
                try:
                    await update.message.delete()
                    warning = f"🚨 **Dangerous URL Detected & Blocked!**\n\n" \
                             f"**URL:** `{url}`\n" \
                             f"**Risk Level:** {result['risk_level'].upper()}\n" \
                             f"**Threat Score:** {result.get('score', 'N/A')}/100\n\n" \
                             f"⚠️ Message automatically removed for your safety.\n" \
                             f"🛡️ This bot protects you from malicious links!"
                    
                    await update.effective_chat.send_message(warning)
                    return True  # URLs were blocked
                except:
                    pass
                return True  # URLs were blocked
        
        return False  # No URLs were blocked

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == "admin_stats":
            if await self.user_manager.is_admin(user_id):
                stats_text = f"📊 **Bot Statistics**\n\n" \
                            f"🤖 **Owner:** {config.BOT_OWNER_NAME}\n" \
                            f"👑 **Admins:** {len(self.user_manager.admins)}\n" \
                            f"🚫 **Banned Users:** {len(self.user_manager.banned_users)}\n" \
                            f"🔄 **Status:** Active ✅\n" \
                            f"🆔 **Your ID:** `{user_id}`"
                
                await query.edit_message_text(stats_text)
            else:
                await query.edit_message_text("❌ Access denied!")
        
        elif query.data == "admin_settings":
            if await self.user_manager.is_admin(user_id):
                settings_text = f"⚙️ **Bot Settings**\n\n" \
                               f"🛡️ **Content Moderation:** Active\n" \
                               f"🔗 **URL Scanner:** Active\n" \
                               f"🤖 **AI Assistant:** Active\n" \
                               f"📁 **File Storage:** Active\n" \
                               f"👑 **Admin Level:** {'Owner' if await self.user_manager.is_owner(user_id) else 'Admin'}"
                
                await query.edit_message_text(settings_text)
            else:
                await query.edit_message_text("❌ Access denied!")

    def run(self):
        """Start the bot with 24/7 reliability"""
        logger.info(f"🚀 Starting 24/7 bot by {config.BOT_OWNER_NAME}")
        
        # Configure for maximum uptime
        retry_attempts = 0
        max_retries = 5
        
        while retry_attempts < max_retries:
            try:
                # Run with automatic restart on network errors
                self.application.run_polling(
                    drop_pending_updates=True,  # Skip old updates on restart
                    close_loop=False,          # Keep event loop alive
                    stop_signals=None          # Don't stop on signals for 24/7 operation
                )
                break  # If successful, break the retry loop
                
            except Exception as e:
                retry_attempts += 1
                logger.error(f"❌ Bot error (attempt {retry_attempts}/{max_retries}): {e}")
                
                if retry_attempts < max_retries:
                    logger.info(f"🔄 Retrying in 10 seconds...")
                    import time
                    time.sleep(10)
                else:
                    logger.error(f"💥 Max retries reached. Bot stopping.")
                    raise

def main():
    """Main function"""
    try:
        bot = TelegramBot()
        bot.run()
    except Exception as e:
        logger.error(f"Bot startup error: {e}")
        print(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()