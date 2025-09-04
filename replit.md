# Telegram Bot Project - Mraprguild's Advanced Bot

## Overview
A comprehensive Telegram bot with advanced features including AI assistance, file management, content moderation, and admin tools.

## Features Implemented
- 🤖 **Gemini AI Assistant** - Powered by Google's Gemini AI for intelligent conversations
- 📁 **File Management System** - Upload/download files of any format with storage channel integration
- 🛡️ **Content Moderation** - Automatic copyright protection, adult content detection, and bad word filtering
- 🔗 **URL Scanner** - Integration with urlscan.io for automatic threat detection
- 👥 **User Management** - Advanced admin tools for user control
- 🚫 **Force Subscribe** - Channel subscription enforcement functionality
- 📊 **User Data Storage** - Automatic saving of user interactions and file metadata

## Architecture
```
bot.py - Main bot application
config.py - Configuration and environment variable management
gemini_ai.py - AI assistant integration
content_moderation.py - Content filtering and safety checks
file_manager.py - File upload/download and storage management
url_scanner.py - URL safety scanning
user_manager.py - User permissions and admin functionality
```

## Admin Commands
- `/admin` - Access admin control panel
- `/ban <user_id>` - Ban a user from the chat
- `/unban <user_id>` - Unban a user
- `/addadmin <user_id>` - Add admin (Owner only)
- `/deladmin <user_id>` - Remove admin (Owner only)
- `/scan <url>` - Scan URL for security threats

## User Commands
- `/start` - Welcome message and feature overview
- `/help` - Complete command list and features
- Text messages - AI assistant responses
- File uploads - Automatic storage and moderation

## Security Features
- Automatic bad word filtering and cleanup
- Adult content detection using AI
- Copyright violation detection
- URL threat scanning with urlscan.io
- Spam content prevention
- Image content analysis

## Channel Integration
- **Storage Channel** - Stores all uploaded files
- **User Data Channel** - Logs user interactions and admin actions
- **Force Subscribe** - Requires subscription to specified channels

## Recent Changes
- Implemented complete bot functionality with all requested features
- Configured environment variable management for secure API key handling
- Set up automated workflows for continuous operation
- Added comprehensive error handling and logging

## Owner Information
- Bot Owner: Mraprguild
- Language: Python
- Framework: python-telegram-bot with asyncio

## Dependencies
All required packages are installed and configured:
- python-telegram-bot (bot framework)
- google-generativeai (AI integration)
- better-profanity, profanity-check (content filtering)
- httpx, requests (HTTP clients)
- pillow, opencv-python (image processing)
- python-magic (file type detection)
- aiofiles (async file operations)

## Status
✅ Bot is configured and running
✅ All features implemented and functional
✅ Environment variables configured
✅ Workflow active and monitoring