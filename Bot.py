
import telebot
from telebot import types
import psycopg2
import os
import datetime
import random
import string
import requests
import json

TOKEN = "7765087926:AAG4N6LY8xIRcSEH9vpt_h3sIZcIkzZZ5po"
ADMIN_ID = 7879820766
CHANNEL_ID = -1003759028487
MIDTRANS_SERVER_KEY = "Mid-server-EVpXi98N5Xk2uRpHViZjeBQu"
MIDTRANS_BASE_URL = "https://app.midtrans.com/snap/v1/transactions"
BOT_USERNAME = "@Maaiq_bot"

bot = telebot.TeleBot(TOKEN)

def db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def setup():
    conn = db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS akun (
        id SERIAL PRIMARY KEY,
        penjual_id BIGINT,
        penjual_nama TEXT,
        kode TEXT UNIQUE,
        detail TEXT,
        harga INTEGER,
        foto TEXT,
        status TEXT,
        tgl TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS trx (
        id SERIAL PRIMARY KEY,
        trx_id TEXT,
        buyer_id BIGINT,
        buyer_nama TEXT,
        seller_id BIGINT,
        akun_id INTEGER,
        harga INTEGER,
        status TEXT,
        midtrans_token TEXT,
        tgl TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS banned (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        tgl TEXT
    )''')
    conn.commit()
    conn.close()

setup()

def buat_kode():
    return "JBAZ" + ''.join(random.choices(string.digits, k=6))

def buat_trx():
    return "TRX" + ''.join(random.choices(string.digits, k=8))

def is_banned(uid):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id FROM banned WHERE user_id=%s", (uid,))
    r = c.fetchone()
    conn.close()
    return r is not None

def menu(uid):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(types.KeyboardButton("🛒 Beli Akun"), types.KeyboardButton("💰 Jual Akun"))
    m.row(types.KeyboardButton("📋 Transaksi"), types.KeyboardButton("ℹ️ Informasi"))
    if uid == ADMIN_ID:
        m.row(types.KeyboardButton("⚙️ Admin Panel"))
    return m

def buat_pembayaran(trx_id, harga, buyer_nama, buyer_id):
    import base64
    auth = base64.b64encode(f"{MIDTRANS_SERVER_KEY}:".encode()).decode()
    payload = {
        "transaction_details": {
            "order_id": trx_id,
            "gross_amount": harga
        },
        "customer_details": {
            "first_name": buyer_nama
        },
        "callbacks": {
            "finish": f"https://t.me/{BOT_USERNAME}"
        }
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth}"
    }
    response = requests.post(MIDTRANS_BASE_URL, json=payload, headers=headers)
    data = response.json()
    return data.get("token"), data.get("redirect_url")

state = {}

@bot.message_handler(commands=['start'])
def start(msg):
    if is_banned(msg.from_user.id):
        bot.reply_to(msg, "❌ Akun kamu dibanned! Hubungi CS.")
        return
    bot.reply_to(msg,
        "🎮 *JBAZ ML ACCOUNT STORE*\n"
        "━━━━━━━━━━━━━━━━━\n"
        "Halo *" + msg.from_user.first_name + "*!\n\n"
        "✅ Escrow Otomatis\n"
        "✅ Garansi 24 Jam\n"
        "✅ Anti Penipuan\n"
        "✅ Proses Cepat\n"
        "━━━━━━━━━━━━━━━━━\n"
        "Pilih menu di bawah!",
        parse_mode="Markdown",
        reply_markup=menu(msg.from_user.id))

@bot.message_handler(func=lambda m: m.text == "ℹ️ Informasi")
def informasi(msg):
    bot.reply_to(msg,
        "ℹ️ *CARA TRANSAKSI*\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "*PENJUAL:*\n"
        "1. Tekan 💰 Jual Akun\n"
        "2. Isi detail akun & harga\n"
        "3. Dapat kode unik (contoh: JBAZ123456)\n"
        "4. Share kode ke pembeli\n"
        "5. Tunggu pembeli bayar\n"
        "6. Uang cair otomatis setelah pembeli konfirmasi\n\n"
        "*PEMBELI:*\n"
        "1. Tekan 🛒 Beli Akun\n"
        "2. Masukkan kode dari penjual\n"
        "3. Cek detail akun\n"
        "4. Bayar via DANA/GoPay/QRIS/Transfer\n"
        "5. Dapat detail akun otomatis\n"
        "6. Konfirmasi akun oke\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        "❓ Ada pertanyaan? Hubungi @FXT82828",
        parse_mode="Markdown",
        reply_markup=menu(msg.from_user.id))

@bot.message_handler(func=lambda m: m.text == "💰 Jual Akun")
def jual(msg):
    if is_banned(msg.from_user.id):
        bot.reply_to(msg, "❌ Akun kamu dibanned!")
        return
    state[msg.from_user.id] = {'step': 'detail'}
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(types.KeyboardButton("Batal"))
    bot.reply_to(msg,
        "💰 *FORM JUAL AKUN*\n"
        "━━━━━━━━━━━━━━━━━\n"
        "Step 1/3\n\n"
        "Tulis detail akun kamu!\n"
        "Contoh:\n"
        "_Rank: Mythic 50 bintang\n"
        "Hero: 80\n"
        "Skin: 45\n"
        "Info: Akun sultan!_",
        parse_mode="Markdown",
        reply_markup=m)

@bot.message_handler(func=lambda m: m.from_user.id in state and state[m.from_user.id].get('step') == 'detail')
def step_detail(msg):
    if msg.text == "Batal":
        state.pop(msg.from_user.id, None)
        bot.reply_to(msg, "❌ Dibatalkan!", reply_markup=menu(msg.from_user.id))
        return
    state[msg.from_user.id]['detail'] = msg.text
    state[msg.from_user.id]['step'] = 'harga'
    bot.reply_to(msg, "Step 2/3\n\n💵 Berapa harga jual? (Rupiah)\nContoh: 500000")

@bot.message_handler(func=lambda m: m.from_user.id in state and state[m.from_user.id].get('step') == 'harga')
def step_harga(msg):
    if msg.text == "Batal":
        state.pop(msg.from_user.id, None)
        bot.reply_to(msg, "❌ Dibatalkan!", reply_markup=menu(msg.from_user.id))
        return
    try:
        harga = int(msg.text)
        if harga < 10000:
            bot.reply_to(msg, "❌ Harga minimal Rp 10.000!")
            return
    except:
        bot.reply_to(msg, "❌ Masukkan angka!")
        return
    state[msg.from_user.id]['harga'] = harga
    state[msg.from_user.id]['step'] = 'foto'
    bot.reply_to(msg, "Step 3/3\n\n📸 Kirim foto screenshot akun ML kamu!")

@bot.message_handler(content_types=['photo'], func=lambda m: m.from_user.id in state and state[m.from_user.id].get('step') == 'foto')
def step_foto(msg):
    foto_id = msg.photo[-1].file_id
    state[msg.from_user.id]['foto'] = foto_id
    state[msg.from_user.id]['step'] = 'konfirmasi'
    data = state[msg.from_user.id]
    mk = types.InlineKeyboardMarkup()
    mk.row(
        types.InlineKeyboardButton("✅ Submit", callback_data="submit_jual"),
        types.InlineKeyboardButton("❌ Batal", callback_data="batal_jual")
    )
    bot.send_photo(msg.chat.id, foto_id,
        caption="📋 *KONFIRMASI AKUN*\n"
        "━━━━━━━━━━━━━━━━━\n"
        "*Detail:*\n" + data['detail'] + "\n\n"
        "*Harga:* Rp " + str(data['harga']) + "\n"
        "━━━━━━━━━━━━━━━━━\n"
        "Data sudah benar?",
        parse_mode="Markdown",
        reply_markup=mk)

@bot.message_handler(func=lambda m: m.text == "🛒 Beli Akun")
def beli(msg):
    if is_banned(msg.from_user.id):
        bot.reply_to(msg, "❌ Akun kamu dibanned!")
        return
    state[msg.from_user.id] = {'step': 'masukkan_kode'}
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(types.KeyboardButton("Batal"))
    bot.reply_to(msg,
        "🛒 *BELI AKUN*\n"
        "━━━━━━━━━━━━━━━━━\n"
        "Masukkan kode dari penjual!\n"
        "Contoh: JBAZ123456",
        parse_mode="Markdown",
        reply_markup=m)

@bot.message_handler(func=lambda m: m.from_user.id in state and state[m.from_user.id].get('step') == 'masukkan_kode')
def step_kode(msg):
    if msg.text == "Batal":
        state.pop(msg.from_user.id, None)
        bot.reply_to(msg, "❌ Dibatalkan!", reply_markup=menu(msg.from_user.id))
        return
    kode = msg.text.upper().strip()
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM akun WHERE kode=%s AND status='tersedia'", (kode,))
    akun = c.fetchone()
    conn.close()
    if not akun:
        bot.reply_to(msg, "❌ Kode tidak ditemukan atau akun sudah terjual!")
        return
    if msg.from_user.id == akun[1]:
        bot.reply_to(msg, "❌ Tidak bisa beli akun sendiri!")
        return
    mk = types.InlineKeyboardMarkup()
    mk.row(
        types.InlineKeyboardButton("✅ Lanjut Beli", callback_data="lanjut_beli_" + str(akun[0])),
        types.InlineKeyboardButton("❌ Batal", callback_data="batal_beli")
    )
    bot.send_photo(msg.chat.id, akun[6],
        caption="📋 *DETAIL AKUN*\n"
        "━━━━━━━━━━━━━━━━━\n"
        "*Kode:* " + kode + "\n"
        "*Detail:*\n" + akun[4] + "\n\n"
        "*Harga:* Rp " + str(akun[5]) + "\n"
        "━━━━━━━━━━━━━━━━━\n"
        "Lanjutkan pembelian?",
        parse_mode="Markdown",
        reply_markup=mk)
    state.pop(msg.from_user.id, None)

@bot.message_handler(func=lambda m: m.text == "📋 Transaksi")
def transaksi(msg):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM trx WHERE buyer_id=%s ORDER BY id DESC LIMIT 5", (msg.from_user.id,))
    list_trx = c.fetchall()
    c.execute("SELECT * FROM akun WHERE penjual_id=%s ORDER BY id DESC LIMIT 5", (msg.from_user.id,))
    list_jual = c.fetchall()
    conn.close()
    teks = "📋 *RIWAYAT TRANSAKSI*\n━━━━━━━━━━━━━━━━━\n\n"
    teks += "*Pembelian:*\n"
    if list_trx:
        for t in list_trx:
            teks += "ID: " + str(t[1]) + "\nHarga: Rp " + str(t[6]) + "\nStatus: " + str(t[7]) + "\n\n"
    else:
        teks += "Belum ada\n\n"
    teks += "*Penjualan:*\n"
    if list_jual:
        for a in list_jual:
            teks += "Kode: " + str(a[3]) + "\nHarga: Rp " + str(a[5]) + "\nStatus: " + str(a[7]) + "\n\n"
    else:
        teks += "Belum ada\n"
    bot.reply_to(msg, teks, parse_mode="Markdown", reply_markup=menu(msg.from_user.id))

@bot.callback_query_handler(func=lambda c: True)
def callback(call):
    uid = call.from_user.id
    nama = call.from_user.first_name

    if call.data == "submit_jual":
        if uid not in state:
            bot.answer_callback_query(call.id, "Session habis!")
            return
        data = state[uid]
        kode = buat_kode()
        tgl = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = db()
        c = conn.cursor()
        c.execute("INSERT INTO akun (penjual_id,penjual_nama,kode,detail,harga,foto,status,tgl) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (uid, nama, kode, data['detail'], data['harga'], data['foto'], 'tersedia', tgl))
        conn.commit()
        conn.close()
        state.pop(uid, None)
        bot.edit_message_caption(
            "✅ *AKUN BERHASIL DIDAFTARKAN!*\n"
            "━━━━━━━━━━━━━━━━━\n"
            "*Kode Unik Kamu:*\n"
            "`" + kode + "`\n\n"
            "Share kode ini ke pembeli!\n"
            "━━━━━━━━━━━━━━━━━\n"
            "⚠️ Jangan share ke orang tidak dikenal!",
            parse_mode="Markdown",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        bot.send_message(uid, "Kembali ke menu!", reply_markup=menu(uid))
        bot.send_message(ADMIN_ID, "📢 Akun baru!\nPenjual: " + nama + "\nKode: " + kode + "\nHarga: Rp " + str(data['harga']))

    elif call.data == "batal_jual":
        state.pop(uid, None)
        bot.edit_message_caption("❌ Dibatalkan!", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(uid, "Kembali ke menu!", reply_markup=menu(uid))

    elif call.data.startswith("lanjut_beli_"):
        akun_id = int(call.data.split("_")[2])
        conn = db()
        c = conn.cursor()
        c.execute("SELECT * FROM akun WHERE id=%s AND status='tersedia'", (akun_id,))
        akun = c.fetchone()
        conn.close()
        if not akun:
            bot.answer_callback_query(call.id, "Akun tidak tersedia!")
            return
        tid = buat_trx()
        tgl = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        token, pay_url = buat_pembayaran(tid, akun[5], nama, uid)
        conn = db()
        c = conn.cursor()
        c.execute("INSERT INTO trx (trx_id,buyer_id,buyer_nama,seller_id,akun_id,harga,status,midtrans_token,tgl) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (tid, uid, nama, akun[1], akun_id, akun[5], 'menunggu_bayar', token, tgl))
        c.execute("UPDATE akun SET status='pending' WHERE id=%s", (akun_id,))
        conn.commit()
        conn.close()
        mk = types.InlineKeyboardMarkup()
        mk.row(types.InlineKeyboardButton("💳 Bayar Sekarang", url=pay_url))
        bot.edit_message_caption(
            "💳 *STRUK ORDER*\n"
            "━━━━━━━━━━━━━━━━━\n"
            "*ID:* " + tid + "\n"
            "*Harga:* Rp " + str(akun[5]) + "\n"
            "━━━━━━━━━━━━━━━━━\n"
            "Klik tombol bayar di bawah!\n"
            "Support: DANA, GoPay, QRIS, Transfer Bank",
            parse_mode="Markdown",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=mk
        )
        bot.send_message(akun[1], "🔔 Ada pembeli!\nID: " + tid + "\nPembeli: " + nama + "\nHarga: Rp " + str(akun[5]))

    elif call.data == "batal_beli":
        bot.edit_message_caption("❌ Dibatalkan!", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(uid, "Kembali ke menu!", reply_markup=menu(uid))

    elif call.data.startswith("oke_"):
        tid = call.data.split("_")[1]
        conn = db()
        c = conn.cursor()
        c.execute("SELECT * FROM trx WHERE trx_id=%s", (tid,))
        trx = c.fetchone()
        c.execute("UPDATE trx SET status='selesai' WHERE trx_id=%s", (tid,))
        c.execute("UPDATE akun SET status='terjual' WHERE id=%s", (trx[5],))
        conn.commit()
        conn.close()
        bot.edit_message_text(
            "✅ *TRANSAKSI SELESAI!*\n"
            "━━━━━━━━━━━━━━━━━\n"
            "ID: " + tid + "\nTerima kasih!",
            parse_mode="Markdown",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        bot.send_message(trx[4], "✅ Transaksi " + tid + " selesai!")
        bot.send_message(ADMIN_ID, "✅ Transaksi " + tid + " selesai!")

    elif call.data.startswith("masalah_"):
        tid = call.data.split("_")[1]
        conn = db()
        c = conn.cursor()
        c.execute("UPDATE trx SET status='dispute' WHERE trx_id=%s", (tid,))
        conn.commit()
        conn.close()
        bot.edit_message_text(
            "⚠️ *LAPORAN DITERIMA!*\n"
            "━━━━━━━━━━━━━━━━━\n"
            "ID: " + tid + "\nAdmin investigasi 1x24 jam!",
            parse_mode="Markdown",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        bot.send_message(ADMIN_ID, "⚠️ DISPUTE!\nTransaksi: " + tid)

@bot.message_handler(commands=['bayar_sukses'])
def bayar_sukses(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        tid = msg.text.split()[1]
    except:
        bot.reply_to(msg, "Format: /bayar_sukses [TRX_ID]")
        return
    proses_pembayaran(tid)
    bot.reply_to(msg, "Pembayaran " + tid + " diproses!")

def proses_pembayaran(tid):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM trx WHERE trx_id=%s", (tid,))
    trx = c.fetchone()
    if not trx:
        conn.close()
        return
    c.execute("SELECT * FROM akun WHERE id=%s", (trx[5],))
    akun = c.fetchone()
    c.execute("UPDATE trx SET status='dibayar' WHERE trx_id=%s", (tid,))
    conn.commit()
    conn.close()
    if akun:
        mk = types.InlineKeyboardMarkup()
        mk.row(
            types.InlineKeyboardButton("✅ Akun Oke", callback_data="oke_" + tid),
            types.InlineKeyboardButton("❌ Ada Masalah", callback_data="masalah_" + tid)
        )
        bot.send_message(trx[2],
            "✅ *PEMBAYARAN DITERIMA!*\n"
            "━━━━━━━━━━━━━━━━━\n"
            "*ID:* " + tid + "\n\n"
            "*Detail Akun:*\n" + akun[4] + "\n\n"
            "━━━━━━━━━━━━━━━━━\n"
            "⚠️ Segera ganti password!\n"
            "Akun sudah sesuai?",
            parse_mode="Markdown",
            reply_markup=mk
        )
        bot.send_message(akun[1], "💰 Pembayaran diterima!\nID: " + tid)

@bot.message_handler(func=lambda m: m.text == "⚙️ Admin Panel")
def admin_panel(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    conn = db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM akun WHERE status='tersedia'")
    stok = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM trx WHERE status='menunggu_bayar'")
    pending = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM trx WHERE status='selesai'")
    selesai = c.fetchone()[0]
    conn.close()
    bot.reply_to(msg,
        "⚙️ *ADMIN PANEL*\n"
        "━━━━━━━━━━━━━━━━━\n"
        "Stok: " + str(stok) + "\n"
        "Pending: " + str(pending) + "\n"
        "Selesai: " + str(selesai) + "\n"
        "━━━━━━━━━━━━━━━━━\n"
        "/bayar\\_sukses [TRX]\n"
        "/ban [ID]\n"
        "/hapus [KODE]",
        parse_mode="Markdown")

@bot.message_handler(commands=['ban'])
def ban(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        target = int(msg.text.split()[1])
    except:
        bot.reply_to(msg, "Format: /ban [USER_ID]")
        return
    tgl = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO banned (user_id,tgl) VALUES (%s,%s)", (target, tgl))
    conn.commit()
    conn.close()
    bot.reply_to(msg, "User " + str(target) + " dibanned!")

@bot.message_handler(commands=['hapus'])
def hapus(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        kode = msg.text.split()[1].upper()
    except:
        bot.reply_to(msg, "Format: /hapus [KODE]")
        return
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE akun SET status='dihapus' WHERE kode=%s", (kode,))
    conn.commit()
    conn.close()
    bot.reply_to(msg, "Akun " + kode + " dihapus!")

bot.delete_webhook()
import time
time.sleep(2)
print("JBAZ Bot aktif!")
bot.polling(none_stop=True)
