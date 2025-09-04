import json
from telegram import Bot, ChatMember
from config import config
import logging
from typing import Dict, List, Optional

class UserManager:
    def __init__(self, bot: Bot):
        """Initialize user manager"""
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.admins = set([config.ADMIN_ID, config.OWNER_ID])
        self.banned_users = set()
        
    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admins
    
    async def is_owner(self, user_id: int) -> bool:
        """Check if user is owner"""
        return user_id == config.OWNER_ID
    
    async def add_admin(self, user_id: int, added_by: int) -> bool:
        """Add new admin (only owner can do this)"""
        if added_by != config.OWNER_ID:
            return False
        
        self.admins.add(user_id)
        await self._save_admin_data(user_id, "added")
        return True
    
    async def remove_admin(self, user_id: int, removed_by: int) -> bool:
        """Remove admin (only owner can do this)"""
        if removed_by != config.OWNER_ID or user_id == config.OWNER_ID:
            return False
        
        self.admins.discard(user_id)
        await self._save_admin_data(user_id, "removed")
        return True
    
    async def ban_user(self, user_id: int, chat_id: int, admin_id: int) -> bool:
        """Ban user from chat"""
        try:
            if not await self.is_admin(admin_id):
                return False
            
            await self.bot.ban_chat_member(chat_id, user_id)
            self.banned_users.add(user_id)
            await self._save_user_action(user_id, "banned", admin_id)
            return True
            
        except Exception as e:
            self.logger.error(f"Ban user error: {e}")
            return False
    
    async def unban_user(self, user_id: int, chat_id: int, admin_id: int) -> bool:
        """Unban user from chat"""
        try:
            if not await self.is_admin(admin_id):
                return False
            
            await self.bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
            self.banned_users.discard(user_id)
            await self._save_user_action(user_id, "unbanned", admin_id)
            return True
            
        except Exception as e:
            self.logger.error(f"Unban user error: {e}")
            return False
    
    async def check_subscription(self, user_id: int, channel_username: str) -> bool:
        """Check if user is subscribed to required channel"""
        try:
            member = await self.bot.get_chat_member(channel_username, user_id)
            return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
            
        except Exception as e:
            self.logger.error(f"Subscription check error: {e}")
            return False
    
    async def save_user_data(self, user_data: dict):
        """Save user data to storage channel"""
        try:
            data_text = f"👤 **User Data**\n" \
                       f"**User ID:** `{user_data.get('user_id')}`\n" \
                       f"**Username:** @{user_data.get('username', 'N/A')}\n" \
                       f"**First Name:** {user_data.get('first_name', 'N/A')}\n" \
                       f"**Data:** ```json\n{json.dumps(user_data, indent=2)}```"
            
            await self.bot.send_message(
                chat_id=config.USER_DATA_SAVE_CHANNEL_ID,
                text=data_text
            )
            
        except Exception as e:
            self.logger.error(f"Save user data error: {e}")
    
    async def _save_admin_data(self, user_id: int, action: str):
        """Save admin action to user data channel"""
        try:
            admin_text = f"👑 **Admin Action**\n" \
                        f"**User ID:** `{user_id}`\n" \
                        f"**Action:** {action}\n" \
                        f"**Timestamp:** {self._get_timestamp()}"
            
            await self.bot.send_message(
                chat_id=config.USER_DATA_SAVE_CHANNEL_ID,
                text=admin_text
            )
            
        except Exception as e:
            self.logger.error(f"Save admin data error: {e}")
    
    async def _save_user_action(self, user_id: int, action: str, admin_id: int):
        """Save user moderation action"""
        try:
            action_text = f"⚖️ **User Action**\n" \
                         f"**User ID:** `{user_id}`\n" \
                         f"**Action:** {action}\n" \
                         f"**Admin ID:** `{admin_id}`\n" \
                         f"**Timestamp:** {self._get_timestamp()}"
            
            await self.bot.send_message(
                chat_id=config.USER_DATA_SAVE_CHANNEL_ID,
                text=action_text
            )
            
        except Exception as e:
            self.logger.error(f"Save user action error: {e}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")