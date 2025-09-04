from flask import Flask, render_template, jsonify
import threading
import os

app = Flask(__name__)

# Import bot instance (this will be set by main.py)
bot_instance = None

@app.route('/')
def dashboard():
    """Main dashboard page"""
    if bot_instance:
        stats = bot_instance.stats
        return render_template('dashboard.html', 
                             bot_name="Advanced Telegram Bot",
                             owner="Bot Owner",
                             stats=stats)
    else:
        return render_template('dashboard.html', 
                             bot_name="Advanced Telegram Bot",
                             owner="Bot Owner",
                             stats=None)

@app.route('/api/stats')
def api_stats():
    """API endpoint for bot statistics"""
    if bot_instance:
        return jsonify(bot_instance.stats)
    else:
        return jsonify({"error": "Bot not initialized"})

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "bot": "running"}

def run_web_interface(bot=None):
    """Run the web interface"""
    global bot_instance
    bot_instance = bot
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
