from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import asyncio
import json
import os
import psutil
import subprocess
from datetime import datetime
from config import config
import httpx
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotStatusChecker:
    def __init__(self):
        self.bot_token = config.BOT_TOKEN
        self.api_keys = {
            'GEMINI_API_KEY': config.GEMINI_API_KEY,
            'URLSCAN_API_KEY': config.URLSCAN_API_KEY,
        }
        
    async def check_bot_connection(self):
        """Check if bot token is valid and bot is reachable"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.telegram.org/bot{self.bot_token}/getMe",
                    timeout=10
                )
                if response.status_code == 200:
                    bot_info = response.json()
                    return {
                        'status': 'connected',
                        'username': bot_info['result']['username'],
                        'name': bot_info['result']['first_name'],
                        'id': bot_info['result']['id']
                    }
                else:
                    return {'status': 'error', 'message': 'Invalid bot token'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    async def check_gemini_api(self):
        """Check Gemini AI API connection"""
        try:
            if not self.api_keys['GEMINI_API_KEY']:
                return {'status': 'not_configured'}
                
            import google.generativeai as genai
            genai.configure(api_key=self.api_keys['GEMINI_API_KEY'])
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Test with a simple query
            response = model.generate_content("Test connection")
            
            return {
                'status': 'connected',
                'model': 'gemini-1.5-flash',
                'response_length': len(response.text) if response.text else 0
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    async def check_urlscan_api(self):
        """Check URLScan.io API connection"""
        try:
            if not self.api_keys['URLSCAN_API_KEY']:
                return {'status': 'not_configured'}
                
            async with httpx.AsyncClient() as client:
                headers = {'API-Key': self.api_keys['URLSCAN_API_KEY']}
                response = await client.get(
                    "https://urlscan.io/api/v1/user/quotas/",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    quota_info = response.json()
                    return {
                        'status': 'connected',
                        'quotas': quota_info
                    }
                else:
                    return {'status': 'error', 'message': f'API returned {response.status_code}'}
                    
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_system_status(self):
        """Get system resource usage"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'uptime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_bot_process_status(self):
        """Check if bot process is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'bot.py' in str(proc.info['cmdline']):
                    return {
                        'status': 'running',
                        'pid': proc.info['pid'],
                        'cpu_percent': proc.cpu_percent(),
                        'memory_mb': proc.memory_info().rss / 1024 / 1024
                    }
            return {'status': 'not_running'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

status_checker = BotStatusChecker()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/bot-status')
async def bot_status():
    """Get bot connection status"""
    try:
        status = await status_checker.check_bot_connection()
        return jsonify(status)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/api-status')
async def api_status():
    """Get all API connection statuses"""
    try:
        gemini_status = await status_checker.check_gemini_api()
        urlscan_status = await status_checker.check_urlscan_api()
        
        return jsonify({
            'gemini': gemini_status,
            'urlscan': urlscan_status
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/system-status')
def system_status():
    """Get system resource status"""
    system_info = status_checker.get_system_status()
    process_info = status_checker.get_bot_process_status()
    
    return jsonify({
        'system': system_info,
        'bot_process': process_info,
        'owner': config.BOT_OWNER_NAME
    })

@app.route('/api/full-status')
async def full_status():
    """Get complete status of all components"""
    try:
        bot_status = await status_checker.check_bot_connection()
        api_statuses = await status_checker.check_gemini_api(), await status_checker.check_urlscan_api()
        system_info = status_checker.get_system_status()
        process_info = status_checker.get_bot_process_status()
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'bot': bot_status,
            'apis': {
                'gemini': api_statuses[0],
                'urlscan': api_statuses[1]
            },
            'system': system_info,
            'process': process_info,
            'owner': config.BOT_OWNER_NAME
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    logger.info(f"🌐 Starting web interface for {config.BOT_OWNER_NAME}'s bot")
    app.run(host='0.0.0.0', port=5000, debug=False)