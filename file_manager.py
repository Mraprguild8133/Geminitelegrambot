import aiofiles
import os
import magic
from telegram import Bot
from config import config
import logging
from typing import Optional
import hashlib

class FileManager:
    def __init__(self, bot: Bot):
        """Initialize file manager"""
        self.bot = bot
        self.storage_channel_id = config.STORAGE_CHANNEL_ID
        self.logger = logging.getLogger(__name__)
        
        # Create uploads directory if it doesn't exist
        self.uploads_dir = "uploads"
        os.makedirs(self.uploads_dir, exist_ok=True)

    async def upload_file_to_storage(self, file_path: str, original_filename: str) -> Optional[str]:
        """Upload file to storage channel and return message ID"""
        try:
            # Get file info
            file_size = os.path.getsize(file_path)
            file_mime = magic.from_file(file_path, mime=True)
            
            # Generate file hash for uniqueness
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            caption = f"📁 **File Storage**\n" \
                     f"**Name:** `{original_filename}`\n" \
                     f"**Size:** {self._format_file_size(file_size)}\n" \
                     f"**Type:** `{file_mime}`\n" \
                     f"**Hash:** `{file_hash}`"

            # Send file to storage channel
            with open(file_path, 'rb') as file:
                message = await self.bot.send_document(
                    chat_id=self.storage_channel_id,
                    document=file,
                    caption=caption,
                    filename=original_filename
                )
            
            return str(message.message_id)
            
        except Exception as e:
            self.logger.error(f"File upload error: {e}")
            return None

    async def download_file_from_storage(self, message_id: str, download_path: str) -> bool:
        """Download file from storage channel"""
        try:
            # Get message from storage channel
            message = await self.bot.get_message(
                chat_id=self.storage_channel_id,
                message_id=int(message_id)
            )
            
            if message.document:
                # Download file
                file = await self.bot.get_file(message.document.file_id)
                await file.download_to_drive(download_path)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"File download error: {e}")
            return False

    async def save_user_file(self, file_path: str, user_id: int, filename: str) -> dict:
        """Save file and return file info"""
        try:
            # Upload to storage channel
            message_id = await self.upload_file_to_storage(file_path, filename)
            
            if message_id:
                file_info = {
                    "user_id": user_id,
                    "filename": filename,
                    "message_id": message_id,
                    "size": os.path.getsize(file_path),
                    "mime_type": magic.from_file(file_path, mime=True)
                }
                
                # Save file info to user data channel
                await self._save_file_info_to_channel(file_info)
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "file_info": file_info
                }
            
            return {"success": False, "error": "Failed to upload file"}
            
        except Exception as e:
            self.logger.error(f"Save user file error: {e}")
            return {"success": False, "error": str(e)}

    async def _save_file_info_to_channel(self, file_info: dict):
        """Save file information to user data channel"""
        try:
            info_text = f"📄 **File Info**\n" \
                       f"**User ID:** `{file_info['user_id']}`\n" \
                       f"**Filename:** `{file_info['filename']}`\n" \
                       f"**Message ID:** `{file_info['message_id']}`\n" \
                       f"**Size:** {self._format_file_size(file_info['size'])}\n" \
                       f"**Type:** `{file_info['mime_type']}`"
            
            await self.bot.send_message(
                chat_id=config.USER_DATA_SAVE_CHANNEL_ID,
                text=info_text
            )
            
        except Exception as e:
            self.logger.error(f"Save file info error: {e}")

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024.0 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"

    def is_supported_file_type(self, filename: str) -> bool:
        """Check if file type is supported"""
        # Support all file types as requested
        return True

    async def cleanup_temp_file(self, file_path: str):
        """Clean up temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")