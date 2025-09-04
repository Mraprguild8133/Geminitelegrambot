import asyncio
import logging
import time
from datetime import datetime
import subprocess
import sys
import os

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class BotKeepAlive:
    def __init__(self):
        self.bot_process = None
        self.restart_count = 0
        self.last_restart = None
        self.max_restarts_per_hour = 10
        
    def start_bot(self):
        """Start the bot process"""
        try:
            logger.info("🚀 Starting bot process...")
            self.bot_process = subprocess.Popen([
                sys.executable, 'bot.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logger.info(f"✅ Bot started with PID: {self.bot_process.pid}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            return False
    
    def is_bot_running(self):
        """Check if bot process is running"""
        if self.bot_process is None:
            return False
        
        # Check if process is still alive
        return self.bot_process.poll() is None
    
    def restart_bot(self):
        """Restart the bot with rate limiting"""
        current_time = time.time()
        
        # Rate limiting: max restarts per hour
        if self.last_restart and (current_time - self.last_restart) < 3600:
            if self.restart_count >= self.max_restarts_per_hour:
                logger.warning(f"⚠️ Too many restarts ({self.restart_count}) in the last hour. Waiting...")
                return False
        else:
            # Reset counter after an hour
            self.restart_count = 0
        
        logger.info("🔄 Restarting bot...")
        
        # Stop current process
        if self.bot_process and self.is_bot_running():
            try:
                self.bot_process.terminate()
                self.bot_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.bot_process.kill()
                self.bot_process.wait()
        
        # Start new process
        if self.start_bot():
            self.restart_count += 1
            self.last_restart = current_time
            logger.info(f"✅ Bot restarted successfully (restart #{self.restart_count})")
            return True
        
        return False
    
    async def monitor_bot(self):
        """Monitor bot health and restart if needed"""
        logger.info("🔍 Starting 24/7 bot monitoring...")
        
        while True:
            try:
                if not self.is_bot_running():
                    logger.warning("⚠️ Bot process not running, attempting restart...")
                    
                    if not self.restart_bot():
                        logger.error("❌ Failed to restart bot, waiting 60 seconds...")
                        await asyncio.sleep(60)
                        continue
                
                # Log status every 30 minutes
                if int(time.time()) % 1800 == 0:  # Every 30 minutes
                    uptime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    logger.info(f"💚 Bot healthy - Uptime check: {uptime}")
                
                # Check every 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Monitor error: {e}")
                await asyncio.sleep(60)
    
    def cleanup(self):
        """Cleanup processes on exit"""
        if self.bot_process and self.is_bot_running():
            logger.info("🛑 Stopping bot process...")
            self.bot_process.terminate()
            try:
                self.bot_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.bot_process.kill()
                self.bot_process.wait()
    
    async def run(self):
        """Main keep-alive loop"""
        try:
            # Initial bot start
            if not self.start_bot():
                logger.error("❌ Failed to start bot initially")
                return
            
            # Start monitoring
            await self.monitor_bot()
            
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested...")
        except Exception as e:
            logger.error(f"❌ Keep-alive error: {e}")
        finally:
            self.cleanup()

def main():
    """Entry point"""
    logger.info("🤖 24/7 Bot Keep-Alive System Starting...")
    keep_alive = BotKeepAlive()
    
    try:
        asyncio.run(keep_alive.run())
    except KeyboardInterrupt:
        logger.info("👋 Keep-alive system stopped")
    except Exception as e:
        logger.error(f"❌ System error: {e}")

if __name__ == "__main__":
    main()