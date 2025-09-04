import logging
import asyncio
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes

from telegram.constants import ChatType

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
        
        # Force subscribe settings
        self.force_subscribe_channels = []  # Add channel usernames here
        
        self.setup_handlers()

    def setup_handlers(self):
        """Setup all command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        self.application.add_handler(CommandHandler("ban", self.ban_command))
        self.application.add_handler(CommandHandler("unban", self.unban_command))
        self.application.add_handler(CommandHandler("addadmin", self.add_admin_command))
        self.application.add_handler(CommandHandler("deladmin", self.del_admin_command))
        self.application.add_handler(CommandHandler("scan", self.scan_url_command))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.application.add_handler(MessageHandler(filters.VIDEO, self.handle_video))
        self.application.add_handler(MessageHandler(filters.AUDIO, self.handle_audio))
        
        # Callback handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Save user data
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "action": "start_command"
        }
        await self.user_manager.save_user_data(user_data)
        
        # Check force subscribe
        if not await self.check_force_subscribe(update, context):
            return
        
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

Ready to assist you! 🚀
        """
        
        await update.message.reply_text(welcome_text)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        if not await self.check_force_subscribe(update, context):
            return
            
        help_text = """
🆘 **Bot Commands & Features**

**🤖 AI Assistant:**
• Just send any text message for AI response
• Ask questions, get help, chat naturally

**📁 File Management:**
• Send any file to store it safely
• Files are automatically uploaded to storage
• All formats supported (documents, images, videos, etc.)

**👑 Admin Commands:**
• `/ban <user_id>` - Ban a user
• `/unban <user_id>` - Unban a user  
• `/addadmin <user_id>` - Add admin (Owner only)
• `/deladmin <user_id>` - Remove admin (Owner only)
• `/admin` - Admin control panel

**🔒 Security Features:**
• `/scan <url>` - Scan URL for threats
• Automatic bad word filtering
• Adult content detection
• Copyright protection
• Spam prevention

**📊 Other Features:**
• Force subscribe functionality
• User data management
• Automatic content moderation
• Advanced file storage system

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
            [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
            [InlineKeyboardButton("📊 Bot Statistics", callback_data="admin_stats")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")],
            [InlineKeyboardButton("🔒 Security", callback_data="admin_security")]
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
        if not await self.check_force_subscribe(update, context):
            return
            
        if not context.args:
            await update.message.reply_text("Usage: `/scan <url>`")
            return
        
        url = context.args[0]
        await update.message.reply_text("🔍 Scanning URL... Please wait.")
        
        result = await self.url_scanner.scan_url(url)
        
        response = f"🔍 **URL Scan Results**\n\n" \
                  f"**URL:** `{url}`\n" \
                  f"**Status:** {result['message']}\n" \
                  f"**Risk Level:** {result['risk_level'].upper()}\n"
        
        if 'score' in result:
            response += f"**Score:** {result['score']}/100\n"
        
        if 'scan_url' in result:
            response += f"**Full Report:** [View Results]({result['scan_url']})"
        
        await update.message.reply_text(response, disable_web_page_preview=True)

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        if not await self.check_force_subscribe(update, context):
            return
        
        text = update.message.text
        user_id = update.effective_user.id
        
        # Check for URLs in message
        urls = self.url_scanner.extract_urls_from_text(text)
        if urls:
            await self.handle_urls_in_message(update, urls)
        
        # Content moderation
        moderation_result = await self.content_moderator.check_text_content(text)
        
        if not moderation_result["is_safe"]:
            # Delete message and warn user
            await update.message.delete()
            
            warning_text = f"⚠️ Message removed due to: {', '.join(moderation_result['violations'])}\n"
            warning_text += "Please follow community guidelines!"
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=warning_text,
                reply_to_message_id=update.message.message_id
            )
            return
        
        # Clean bad words if present
        if moderation_result["violations"]:
            cleaned_text = moderation_result["cleaned_text"]
        else:
            cleaned_text = text
        
        # Generate AI response
        await update.message.reply_text("🤖 Thinking...")
        
        ai_response = await self.gemini_ai.generate_response(
            cleaned_text, 
            f"User ID: {user_id}, Chat: {update.effective_chat.type}"
        )
        
        # Split long messages
        if len(ai_response) > 4000:
            for i in range(0, len(ai_response), 4000):
                await update.message.reply_text(ai_response[i:i+4000])
        else:
            await update.message.reply_text(ai_response)

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads"""
        if not await self.check_force_subscribe(update, context):
            return
        
        await self.process_file_upload(update, context, update.message.document)

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo uploads"""
        if not await self.check_force_subscribe(update, context):
            return
        
        photo = update.message.photo[-1]  # Get highest resolution
        await self.process_file_upload(update, context, photo)

    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video uploads"""
        if not await self.check_force_subscribe(update, context):
            return
        
        await self.process_file_upload(update, context, update.message.video)

    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle audio uploads"""
        if not await self.check_force_subscribe(update, context):
            return
        
        await self.process_file_upload(update, context, update.message.audio)

    async def process_file_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_obj):
        """Process file upload with content moderation"""
        try:
            await update.message.reply_text("📁 Processing your file...")
            
            # Get file
            file = await context.bot.get_file(file_obj.file_id)
            
            # Generate filename
            filename = getattr(file_obj, 'file_name', f"file_{file_obj.file_id}")
            if not filename:
                filename = f"file_{file_obj.file_id}.unknown"
            
            file_path = os.path.join("uploads", filename)
            
            # Download file
            await file.download_to_drive(file_path)
            
            # Content moderation for images
            if hasattr(file_obj, 'width'):  # It's an image
                moderation_result = await self.content_moderator.check_image_content(file_path)
                if not moderation_result["is_safe"]:
                    await update.message.delete()
                    await update.message.reply_text(f"❌ File removed: {moderation_result['reason']}")
                    await self.file_manager.cleanup_temp_file(file_path)
                    return
            
            # Save file
            result = await self.file_manager.save_user_file(
                file_path, update.effective_user.id, filename
            )
            
            if result["success"]:
                response = f"✅ **File Saved Successfully!**\n\n" \
                          f"📁 **Filename:** `{filename}`\n" \
                          f"🆔 **File ID:** `{result['message_id']}`\n" \
                          f"📊 **Size:** {self.file_manager._format_file_size(result['file_info']['size'])}\n" \
                          f"🔗 **Type:** `{result['file_info']['mime_type']}`"
                
                await update.message.reply_text(response)
            else:
                await update.message.reply_text(f"❌ Failed to save file: {result['error']}")
            
            # Cleanup
            await self.file_manager.cleanup_temp_file(file_path)
            
        except Exception as e:
            logger.error(f"File upload error: {e}")
            await update.message.reply_text("❌ Error processing file. Please try again.")

    async def handle_urls_in_message(self, update: Update, urls: list):
        """Handle URLs found in messages"""
        for url in urls:
            result = await self.url_scanner.scan_url(url)
            
            if not result["is_safe"] and result["risk_level"] in ["high", "medium"]:
                await update.message.delete()
                
                warning = f"🚨 **Dangerous URL Detected!**\n\n" \
                         f"**URL:** `{url}`\n" \
                         f"**Risk:** {result['risk_level'].upper()}\n" \
                         f"**Reason:** {result['message']}\n\n" \
                         f"Message has been removed for safety."
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=warning
                )
                break

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("admin_"):
            await self.handle_admin_callback(query, context)
        elif query.data.startswith("subscribe_"):
            await self.handle_subscribe_callback(query, context)

    async def handle_admin_callback(self, query, context):
        """Handle admin panel callbacks"""
        if not await self.user_manager.is_admin(query.from_user.id):
            await query.edit_message_text("❌ Access denied!")
            return
        
        if query.data == "admin_stats":
            stats_text = f"📊 **Bot Statistics**\n\n" \
                        f"🤖 **Owner:** {config.BOT_OWNER_NAME}\n" \
                        f"👑 **Admins:** {len(self.user_manager.admins)}\n" \
                        f"🚫 **Banned Users:** {len(self.user_manager.banned_users)}\n" \
                        f"🔄 **Status:** Active ✅"
            
            await query.edit_message_text(stats_text)

    async def handle_subscribe_callback(self, query, context):
        """Handle force subscribe callbacks"""
        if query.data == "subscribe_check":
            user_id = query.from_user.id
            
            # Check subscription status
            all_subscribed = True
            for channel in self.force_subscribe_channels:
                if not await self.user_manager.check_subscription(user_id, channel):
                    all_subscribed = False
                    break
            
            if all_subscribed:
                await query.edit_message_text("✅ Thank you for subscribing! You can now use the bot.")
            else:
                await query.answer("❌ Please subscribe to all required channels first!")

    async def check_force_subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check force subscribe requirements"""
        if not self.force_subscribe_channels:
            return True
        
        user_id = update.effective_user.id
        
        # Skip check for admins
        if await self.user_manager.is_admin(user_id):
            return True
        
                # Check subscription to all required channels
         channel in self.force_subscribe_channels:
            if not await self.user_manager.check_subscription(user_id, channel):
                # Create subscribe buttons
                keyboard = []
                for ch in self.force_subscribe_channels:
                    keyboard.append([InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch.lstrip('@')}")])
                
                keyboard.append([InlineKeyboardButton("✅ Check Subscription", callback_data="subscribe_check")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                subscribe_text = "🔒 **Access Restricted**\n\n" \
                               "Please subscribe to our channels to use this bot:\n\n" \
                               + "\n".join([f"📢 {ch}" for ch in self.force_subscribe_channels])
                
                await update.message.reply_text(subscribe_text, reply_markup=reply_markup)
                return False
        
        return True

    async def run(self):
        """Start the bot"""
        logger.info(f"Starting bot by {config.BOT_OWNER_NAME}")
        await self.application.run_polling()

def main():
    """Main function"""
    bot = TelegramBot()
    asyncio.run(bot.run())

if __name__ == "__main__":
    main()
