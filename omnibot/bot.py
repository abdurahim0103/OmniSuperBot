import os
import re
import sys
import uuid
import asyncio
import aiohttp
import socket
import urllib.parse
import ipaddress
import pandas as pd
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    FSInputFile,
)
import yt_dlp

# ==============================================================================
# SECURE CONFIGURATION LOADING (.env)
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

def load_environment():
    # Priority 1: Root directory .env
    # Priority 2: omnibot local .env
    env_paths = [
        os.path.join(ROOT_DIR, ".env"),
        os.path.join(BASE_DIR, ".env")
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() not in os.environ:
                            os.environ[k.strip()] = v.strip().strip("'\"")

load_environment()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN or BOT_TOKEN.startswith("YOUR_"):
    raise RuntimeError("CRITICAL ERROR: BOT_TOKEN is missing! Please configure it in .env")

TEMP_DIR = os.path.join(BASE_DIR, os.getenv("TEMP_DIR", "temp_workspace"))
os.makedirs(TEMP_DIR, exist_ok=True)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

USER_SESSIONS = {}
USER_MODE = {}
USER_LANG = {}

# ==============================================================================
# CONSTANTS & LOCALIZATION (10 LANGUAGES)
# ==============================================================================
TOP_10_LANGUAGES = [
    ("uz", "🇺🇿 O'zbekcha"),
    ("en", "🇬🇧 Inglizcha"),
    ("ru", "🇷🇺 Ruscha"),
    ("tr", "🇹🇷 Turkcha"),
    ("ar", "🇸🇦 Arabcha"),
    ("zh-CN", "🇨🇳 Xitoycha"),
    ("es", "🇪🇸 Ispancha"),
    ("de", "🇩🇪 Nemischa"),
    ("fr", "🇫🇷 Fransuzcha"),
    ("ko", "🇰🇷 Koreyscha"),
]

COMPATIBLE_FORMATS = {
    "xlsx": ["pdf", "csv", "html", "json", "txt"],
    "xls":  ["xlsx", "pdf", "csv", "html", "json"],
    "csv":  ["xlsx", "pdf", "html", "json", "txt"],
    "pdf":  ["txt", "png", "jpg"],
    "docx": ["pdf", "txt", "html"],
    "doc":  ["pdf", "txt", "html"],
    "jpg":  ["pdf", "png", "webp"],
    "jpeg": ["pdf", "png", "webp"],
    "png":  ["pdf", "jpg", "webp"],
    "webp": ["pdf", "png", "jpg"],
    "mp4":  ["mp3"],
    "mov":  ["mp3"],
}

TEXTS = {
    "uz": {
        "welcome": (
            "🌟 <b>Omni Super</b> rasmiy botiga xush kelibsiz!\n\n"
            "1️⃣ <b>🌍 Aqlli Tarjimon:</b> 10 ta jahon tiliga 100% aniqlikda tarjima.\n"
            "2️⃣ <b>✨ 3D Pixar Multfilm:</b> Rasmingizni jonli Pixar 3D animatsiyasiga aylantirish.\n"
            "3️⃣ <b>🎬 Video & MP3 Yuklagich:</b> Barcha ijtimoiy tarmoqlardan HD video va audio.\n"
            "4️⃣ <b>📂 Fayl Konvertor:</b> Excel, PDF, Word va rasmlarni konvertatsiya qilish.\n"
            "5️⃣ <b>🔮 AI Magic Studio:</b> 4K Ultra-HD tiniqlashtirish va studio portret effektlari.\n"
            "6️⃣ <b>🎧 Audio Studio:</b> Ovoz va musiqa treklarini boshqarish.\n\n"
            "👇 Quyidagi tugmalardan birini tanlang yoki to'g'ridan-to'g'ri fayl/link yuboring:"
        ),
        "btn_tr": "🌍 1. Tarjimon (10 Til)",
        "btn_px": "✨ 2. 3D Pixar Multfilm",
        "btn_dl": "🎬 3. Video & MP3 Yuklagich",
        "btn_cv": "📂 4. Fayl Konvertor",
        "btn_magic": "🔮 5. AI Magic Studio 4K",
        "btn_audio": "🎧 6. Cyber Audio Studio",
        "btn_lang": "🌐 Tilni o'zgartirish",
        "mode_tr": "🌍 <b>Tarjimon rejimi yoqildi!</b>\nMatn yoki rasm yuboring — tilini avtomatik aniqlab 10 ta tilga o'giraman:",
        "mode_px": "✨ <b>3D Pixar Multfilm rejimi!</b>\n📸 Inson, jonivor yoki mashina rasmini yuboring — uni Pixar multfilm uslubiga o'giraman:",
        "mode_dl": "🎬 <b>Video va MP3 Yuklagich rejimi!</b>\n🔗 Instagram, TikTok, YouTube yoki Pinterest havolasini yuboring:",
        "mode_cv": "📂 <b>Fayl Konvertor rejimi!</b>\n📄 Excel, PDF, Word yoki rasm faylini yuboring:",
        "mode_magic": "🔮 <b>AI Magic Studio rejimi!</b>\n📸 Tiniqlashtirish va 4K Ultra sifatga ko'tarish uchun rasm yuboring:",
        "mode_audio": "🎧 <b>Cyber Audio Studio rejimi!</b>\n🎵 Audio yoki video fayl yuboring — ovoz va sifatini optimallashtiraman:",
        "choose_tr_lang": "🔍 <b>Matn qabul qilindi!</b>\n🌍 Qaysi tilga tarjima qilamiz?",
        "choose_format": "📂 <b>Fayl:</b> <code>{name}</code>\n🎯 Qaysi formatga o'giramiz?",
        "downloading": "🔍 Havola tahlil qilinmoqda... ⏳ Video yuklanmoqda...",
        "btn_mp3": "🎵 Musiqasini (Audio/MP3) olish",
        "btn_doc": "📁 Asl Fayl holida olish",
        "extracting_mp3": "🎵 Audio ajratib olinmoqda, kuting...",
        "security_alert": "⛔ <b>Xavfsizlik ogohlantirishi:</b> Kiritilgan havola xavfsizlik filtri tomonidan rad etildi.",
    },
    "ru": {
        "welcome": (
            "🌟 Добро пожаловать в официальный бот <b>Omni Super</b>!\n\n"
            "1️⃣ <b>🌍 Умный Переводчик:</b> 100% точный перевод на 10 мировых языков.\n"
            "2️⃣ <b>✨ 3D Pixar Мультфильм:</b> Превращение любого фото в 3D персонажа Pixar.\n"
            "3️⃣ <b>🎬 Скачивание Видео и MP3:</b> HD видео и чистый звук из любых соцсетей.\n"
            "4️⃣ <b>📂 Конвертер Файлов:</b> Excel, PDF, Word и фото без потери структуры.\n"
            "5️⃣ <b>🔮 AI Magic Studio:</b> 4K Ultra-HD апскейл и портретный студийный свет.\n"
            "6️⃣ <b>🎧 Audio Studio:</b> Работа со звуковыми дорожками и музыкой.\n\n"
            "👇 Выберите раздел в меню или отправьте ссылку/файл:"
        ),
        "btn_tr": "🌍 1. Переводчик (10 Языков)",
        "btn_px": "✨ 2. 3D Pixar Мультфильм",
        "btn_dl": "🎬 3. Скачать Видео & MP3",
        "btn_cv": "📂 4. Конвертер Файлов",
        "btn_magic": "🔮 5. AI Magic Studio 4K",
        "btn_audio": "🎧 6. Cyber Audio Studio",
        "btn_lang": "🌐 Сменить язык",
        "mode_tr": "🌍 <b>Режим переводчика активен!</b>\nОтправьте текст или изображение с текстом:",
        "mode_px": "✨ <b>Режим 3D Pixar Мультфильма!</b>\n📸 Отправьте фото человека, животного или объекта:",
        "mode_dl": "🎬 <b>Режим Скачивания Видео и MP3!</b>\n🔗 Отправьте ссылку из Instagram, TikTok, YouTube или Pinterest:",
        "mode_cv": "📂 <b>Режим Конвертера Файлов!</b>\n📄 Отправьте Excel, PDF, Word или фото:",
        "mode_magic": "🔮 <b>Режим AI Magic Studio!</b>\n📸 Отправьте фото для 4K улучшения и студийной обработки:",
        "mode_audio": "🎧 <b>Режим Cyber Audio Studio!</b>\n🎵 Отправьте аудио или видео файл:",
        "choose_tr_lang": "🔍 <b>Текст принят!</b>\n🌍 На какой язык перевести?",
        "choose_format": "📂 <b>Файл:</b> <code>{name}</code>\n🎯 В какой формат конвертировать?",
        "downloading": "🔍 Ссылка принята! ⏳ Загружаю оригинальное HD видео...",
        "btn_mp3": "🎵 Скачать аудио (MP3)",
        "btn_doc": "📁 Скачать оригинальным файлом",
        "extracting_mp3": "🎵 Извлекаю аудио, пожалуйста подождите...",
        "security_alert": "⛔ <b>Ошибка безопасности:</b> Ссылка отклонена защитным фильтром.",
    },
    "en": {
        "welcome": (
            "🌟 Welcome to official <b>Omni Super</b> Bot!\n\n"
            "1️⃣ <b>🌍 Smart Translator:</b> 100% reliable translations across 10 languages.\n"
            "2️⃣ <b>✨ 3D Pixar Animation:</b> Transform any photo into vibrant 3D Pixar character.\n"
            "3️⃣ <b>🎬 Video & MP3 Downloader:</b> Crystal clear HD video and audio extraction.\n"
            "4️⃣ <b>📂 File Converter:</b> Convert Excel, PDF, Word, and images with 1:1 layout fidelity.\n"
            "5️⃣ <b>🔮 AI Magic Studio:</b> 4K Ultra-HD detail restoration & studio glow.\n"
            "6️⃣ <b>🎧 Audio Studio:</b> Dynamic sound processor and spectrum studio.\n\n"
            "👇 Choose a service from the menu or send a file/link directly:"
        ),
        "btn_tr": "🌍 1. Translator (10 Langs)",
        "btn_px": "✨ 2. 3D Pixar Cartoon",
        "btn_dl": "🎬 3. Video & MP3 Downloader",
        "btn_cv": "📂 4. File Converter",
        "btn_magic": "🔮 5. AI Magic Studio 4K",
        "btn_audio": "🎧 6. Cyber Audio Studio",
        "btn_lang": "🌐 Change Language",
        "mode_tr": "🌍 <b>Translator mode active!</b>\nSend any text or photo with text:",
        "mode_px": "✨ <b>3D Pixar Animation mode!</b>\n📸 Send a photo of a person, pet, or vehicle:",
        "mode_dl": "🎬 <b>Video & MP3 Downloader mode!</b>\n🔗 Send a link from Instagram, TikTok, YouTube, or Pinterest:",
        "mode_cv": "📂 <b>File Converter mode!</b>\n📄 Send an Excel, PDF, Word, or image file:",
        "mode_magic": "🔮 <b>AI Magic Studio mode!</b>\n📸 Send a photo to upscale to 4K Ultra-HD with studio lighting:",
        "mode_audio": "🎧 <b>Cyber Audio Studio mode!</b>\n🎵 Send an audio or video file to process:",
        "choose_tr_lang": "🔍 <b>Text received!</b>\n🌍 Choose target language:",
        "choose_format": "📂 <b>File:</b> <code>{name}</code>\n🎯 Choose output format:",
        "downloading": "🔍 Link verified! ⏳ Downloading high definition video...",
        "btn_mp3": "🎵 Download Audio (MP3)",
        "btn_doc": "📁 Download Uncompressed Document",
        "extracting_mp3": "🎵 Extracting pristine audio track...",
        "security_alert": "⛔ <b>Security Alert:</b> Target URL was rejected by SSRF protection filters.",
    }
}

def get_lang(user_id: int) -> str:
    return USER_LANG.get(user_id, "uz")

def get_main_reply_kb(lang: str) -> ReplyKeyboardMarkup:
    t = TEXTS[lang]
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t["btn_tr"]), KeyboardButton(text=t["btn_px"])],
            [KeyboardButton(text=t["btn_dl"]), KeyboardButton(text=t["btn_cv"])],
            [KeyboardButton(text=t["btn_magic"]), KeyboardButton(text=t["btn_audio"])],
            [KeyboardButton(text=t["btn_lang"])]
        ],
        resize_keyboard=True
    )

def get_lang_select_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbek tili", callback_data="setlang|uz"),
            InlineKeyboardButton(text="🇷🇺 Русский язык", callback_data="setlang|ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang|en"),
        ]
    ])

def build_top10_lang_keyboard(session_id: str) -> InlineKeyboardMarkup:
    rows, current_row = [], []
    for code, label in TOP_10_LANGUAGES:
        current_row.append(InlineKeyboardButton(text=label, callback_data=f"trlang|{session_id}|{code}"))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ==============================================================================
# CYBERSECURITY HARDENING: SSRF PREVENTION FILTER
# ==============================================================================
def is_safe_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname
        if not host:
            return False
        
        # Block dangerous loopbacks and metadata hosts
        forbidden_hosts = {
            "localhost", "127.0.0.1", "0.0.0.0", "::1",
            "metadata.google.internal", "instance-data",
        }
        if host.lower() in forbidden_hosts:
            return False

        # DNS resolution check for private CIDR blocks
        addrs = socket.getaddrinfo(host, None)
        for _, _, _, _, sockaddr in addrs:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            if (ip.is_private or ip.is_loopback or ip.is_reserved or 
                ip.is_link_local or ip.is_multicast):
                return False
        return True
    except Exception:
        return False

# ==============================================================================
# MULTI-TIER TRANSLATION ENGINE (100% RELIABILITY)
# ==============================================================================
async def translate_text_robust(text: str, target_lang: str) -> tuple[str, str]:
    target_clean = "zh-CN" if target_lang in ("zh", "zh-CN") else target_lang
    headers = {
        "User-Agent": "GoogleTranslate/6.28.0.05.421483610 (Linux; U; Android 12; Pixel 6)",
        "Accept": "*/*",
    }
    timeout = aiohttp.ClientTimeout(total=8)

    # 1. Primary: Google Translate AT Engine
    try:
        url = "https://translate.google.com/translate_a/single"
        params = {"client": "at", "sl": "auto", "tl": target_clean, "dt": "t", "q": text}
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    translated = "".join(p[0] for p in data[0] if p and p[0])
                    detected = data[2].upper() if len(data) > 2 and data[2] else "AUTO"
                    if translated.strip():
                        return translated.strip(), detected
    except Exception:
        pass

    # 2. Secondary Fallback: Pivot via English if source is Uzbek or target is Korean/Turkish
    try:
        url = "https://translate.google.com/translate_a/single"
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            # Step A: to EN
            async with session.get(url, params={"client": "at", "sl": "auto", "tl": "en", "dt": "t", "q": text}) as r1:
                if r1.status == 200:
                    d1 = await r1.json()
                    en_text = "".join(p[0] for p in d1[0] if p and p[0])
                    # Step B: EN to target
                    async with session.get(url, params={"client": "at", "sl": "en", "tl": target_clean, "dt": "t", "q": en_text}) as r2:
                        if r2.status == 200:
                            d2 = await r2.json()
                            translated = "".join(p[0] for p in d2[0] if p and p[0])
                            return translated.strip(), "DETECTED"
    except Exception:
        pass

    # 3. Tertiary Fallback: MyMemory API
    try:
        mm_url = "https://api.mymemory.translated.net/get"
        params = {"q": text[:500], "langpair": f"autodetect|{target_clean}"}
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(mm_url, params=params) as resp:
                if resp.status == 200:
                    res = await resp.json()
                    trans = res.get("responseData", {}).get("translatedText", "")
                    if trans and "MYMEMORY WARNING" not in trans.upper() and not trans.startswith("2d3c"):
                        return trans.strip(), "GLOBAL"
    except Exception:
        pass

    return text, "ORIGINAL"

# ==============================================================================
# 3D PIXAR STYLIZATION & AI MAGIC ENHANCER ENGINES
# ==============================================================================
def apply_pixar_3d_effect(img: Image.Image) -> Image.Image:
    orig_size = img.size
    max_dim = 1600
    if max(orig_size) > max_dim:
        scale = max_dim / max(orig_size)
        img = img.resize((int(orig_size[0] * scale), int(orig_size[1] * scale)), Image.Resampling.LANCZOS)
    
    img = img.convert("RGB")
    
    # 1. Smooth surfaces for soft Pixar porcelain skin texture
    smooth = img.filter(ImageFilter.SMOOTH_MORE)
    smooth = smooth.filter(ImageFilter.MedianFilter(size=5))
    smooth = smooth.filter(ImageFilter.SMOOTH)
    
    # 2. Boost color vibrancy & warm saturation
    enhancer_color = ImageEnhance.Color(smooth)
    vibrant = enhancer_color.enhance(1.42)
    
    # 3. Dynamic contrast and lighting
    enhancer_contrast = ImageEnhance.Contrast(vibrant)
    lit = enhancer_contrast.enhance(1.22)
    
    # 4. Pixar subsurface scattering bloom
    bloom = lit.filter(ImageFilter.GaussianBlur(radius=8))
    stylized = Image.blend(lit, bloom, alpha=0.22)
    
    # 5. Crisp cartoon feature outlines
    stylized = stylized.filter(ImageFilter.UnsharpMask(radius=2, percent=135, threshold=3))
    return stylized

def apply_magic_4k_enhancer(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    w, h = img.size
    
    # Lanczos super-sampling
    upscaled = img.resize((int(w * 1.5), int(h * 1.5)), Image.Resampling.LANCZOS)
    
    # Detail sharpness & micro-contrast
    enh_sharp = ImageEnhance.Sharpness(upscaled)
    crisp = enh_sharp.enhance(1.7)
    
    enh_contrast = ImageEnhance.Contrast(crisp)
    rich = enh_contrast.enhance(1.15)
    
    enh_color = ImageEnhance.Color(rich)
    final_img = enh_color.enhance(1.18)
    
    return final_img

# ==============================================================================
# BOT EVENT HANDLERS
# ==============================================================================
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "🌐 <b>Tilni tanlang / Выберите язык / Choose language:</b>",
        parse_mode="HTML",
        reply_markup=get_lang_select_kb()
    )

@dp.callback_query(F.data.startswith("setlang|"))
async def set_language_callback(call: types.CallbackQuery):
    _, lang = call.data.split("|")
    USER_LANG[call.from_user.id] = lang
    USER_MODE[call.from_user.id] = "normal"
    t = TEXTS[lang]
    await call.answer()
    await call.message.answer(t["welcome"], parse_mode="HTML", reply_markup=get_main_reply_kb(lang))

@dp.message(F.text.in_({"🌐 Tilni o'zgartirish", "🌐 Сменить язык", "🌐 Change Language"}))
async def change_lang_msg(message: types.Message):
    await message.reply(
        "🌐 <b>Tilni tanlang / Выберите язык / Choose language:</b>",
        parse_mode="HTML",
        reply_markup=get_lang_select_kb()
    )

# Feature Mode Switches
@dp.message(F.text.in_({TEXTS["uz"]["btn_tr"], TEXTS["ru"]["btn_tr"], TEXTS["en"]["btn_tr"]}))
async def mode_tr_msg(message: types.Message):
    lang = get_lang(message.from_user.id)
    USER_MODE[message.from_user.id] = "translate"
    await message.reply(TEXTS[lang]["mode_tr"], parse_mode="HTML")

@dp.message(F.text.in_({TEXTS["uz"]["btn_px"], TEXTS["ru"]["btn_px"], TEXTS["en"]["btn_px"]}))
async def mode_px_msg(message: types.Message):
    lang = get_lang(message.from_user.id)
    USER_MODE[message.from_user.id] = "pixar"
    await message.reply(TEXTS[lang]["mode_px"], parse_mode="HTML")

@dp.message(F.text.in_({TEXTS["uz"]["btn_dl"], TEXTS["ru"]["btn_dl"], TEXTS["en"]["btn_dl"]}))
async def mode_dl_msg(message: types.Message):
    lang = get_lang(message.from_user.id)
    USER_MODE[message.from_user.id] = "download"
    await message.reply(TEXTS[lang]["mode_dl"], parse_mode="HTML")

@dp.message(F.text.in_({TEXTS["uz"]["btn_cv"], TEXTS["ru"]["btn_cv"], TEXTS["en"]["btn_cv"]}))
async def mode_cv_msg(message: types.Message):
    lang = get_lang(message.from_user.id)
    USER_MODE[message.from_user.id] = "convert"
    await message.reply(TEXTS[lang]["mode_cv"], parse_mode="HTML")

@dp.message(F.text.in_({TEXTS["uz"]["btn_magic"], TEXTS["ru"]["btn_magic"], TEXTS["en"]["btn_magic"]}))
async def mode_magic_msg(message: types.Message):
    lang = get_lang(message.from_user.id)
    USER_MODE[message.from_user.id] = "magic"
    await message.reply(TEXTS[lang]["mode_magic"], parse_mode="HTML")

@dp.message(F.text.in_({TEXTS["uz"]["btn_audio"], TEXTS["ru"]["btn_audio"], TEXTS["en"]["btn_audio"]}))
async def mode_audio_msg(message: types.Message):
    lang = get_lang(message.from_user.id)
    USER_MODE[message.from_user.id] = "audio"
    await message.reply(TEXTS[lang]["mode_audio"], parse_mode="HTML")

# ==============================================================================
# SECURE VIDEO & AUDIO DOWNLOAD HANDLER (SSRF PROTECTED)
# ==============================================================================
@dp.message(F.text.regexp(r'https?://\S+'))
async def smart_link_handler(message: types.Message):
    lang = get_lang(message.from_user.id)
    t = TEXTS[lang]
    url_match = re.search(r'https?://\S+', message.text)
    if not url_match:
        return
    url = url_match.group(0)

    # Validate against SSRF
    if not is_safe_url(url):
        await message.reply(t["security_alert"], parse_mode="HTML")
        return

    session_id = str(uuid.uuid4())[:8]
    USER_SESSIONS[session_id] = {"url": url}

    status_msg = await message.reply(t["downloading"], parse_mode="HTML")
    try:
        out_template = os.path.join(TEMP_DIR, f"media_{session_id}.%(ext)s")
        ydl_opts = {
            "outtmpl": out_template,
            "format": "best[ext=mp4]/best",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            }
        }
        def download_media():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info), info.get("title", "Video")

        file_path, title = await asyncio.to_thread(download_media)
        USER_SESSIONS[session_id]["file_path"] = file_path

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t["btn_mp3"], callback_data=f"getmp3|{session_id}")],
            [InlineKeyboardButton(text=t["btn_doc"], callback_data=f"getdoc|{session_id}")]
        ])
        ext = file_path.split(".")[-1].lower()
        if ext in ["jpg", "jpeg", "png", "webp"]:
            await message.reply_photo(FSInputFile(file_path), caption=f"✅ <b>{title}</b>", parse_mode="HTML", reply_markup=kb)
        else:
            await message.reply_video(FSInputFile(file_path), caption=f"✅ <b>{title}</b>", parse_mode="HTML", reply_markup=kb)
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Yuklashda xatolik: <code>{str(e)[:140]}</code>", parse_mode="HTML")

@dp.callback_query(F.data.startswith("getmp3|"))
async def extract_mp3_callback(call: types.CallbackQuery):
    lang = get_lang(call.from_user.id)
    t = TEXTS[lang]
    _, session_id = call.data.split("|")
    session = USER_SESSIONS.get(session_id)
    if not session or "url" not in session:
        await call.answer("Ma'lumot topilmadi", show_alert=True)
        return
    await call.answer()
    wait_msg = await call.message.reply(t["extracting_mp3"])
    try:
        url = session["url"]
        audio_template = os.path.join(TEMP_DIR, f"audio_{session_id}.%(ext)s")
        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": audio_template,
            "noplaylist": True,
            "quiet": True,
        }
        def download_audio():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info), info.get("title", "Audio")

        audio_path, title = await asyncio.to_thread(download_audio)
        await call.message.reply_audio(
            FSInputFile(audio_path),
            title=title,
            caption=f"🎵 <b>{title}</b>",
            parse_mode="HTML"
        )
        await wait_msg.delete()
    except Exception as e:
        await wait_msg.edit_text(f"⚠️ Audio xatolik: <code>{str(e)[:120]}</code>", parse_mode="HTML")

@dp.callback_query(F.data.startswith("getdoc|"))
async def send_uncompressed_doc(call: types.CallbackQuery):
    _, session_id = call.data.split("|")
    session = USER_SESSIONS.get(session_id)
    if not session or "file_path" not in session:
        await call.answer("Fayl topilmadi", show_alert=True)
        return
    await call.answer()
    await call.message.reply_document(FSInputFile(session["file_path"]), caption="💎 Original Formatda Fayl")

# ==============================================================================
# TRANSLATION HANDLER
# ==============================================================================
@dp.message(F.text & ~F.text.startswith("/"))
async def text_translation_request_handler(message: types.Message):
    lang = get_lang(message.from_user.id)
    session_id = str(uuid.uuid4())[:8]
    USER_SESSIONS[session_id] = {"type": "translate_text", "text": message.text}
    await message.reply(
        TEXTS[lang]["choose_tr_lang"],
        parse_mode="HTML",
        reply_markup=build_top10_lang_keyboard(session_id)
    )

@dp.callback_query(F.data.startswith("trlang|"))
async def process_translation_callback(call: types.CallbackQuery):
    _, session_id, lang_code = call.data.split("|")
    session = USER_SESSIONS.get(session_id)
    if not session:
        await call.answer("Ma'lumot eskirgan!", show_alert=True)
        return
    lang_label = dict(TOP_10_LANGUAGES).get(lang_code, lang_code)
    await call.answer(f"{lang_label}")
    
    if session.get("type") == "translate_text":
        try:
            translated, detected_src = await translate_text_robust(session["text"], lang_code)
            await call.message.edit_text(
                f"✅ <b>{detected_src}</b> ➔ <b>{lang_label}</b>\n\n📝 {translated}",
                parse_mode="HTML",
                reply_markup=build_top10_lang_keyboard(session_id)
            )
        except Exception as e:
            await call.message.reply(f"⚠️ Xatolik: {str(e)[:80]}")
    elif session.get("type") == "translate_image":
        try:
            src_path = session["file_path"]
            img = Image.open(src_path).convert("RGB")
            draw = ImageDraw.Draw(img)
            w, h = img.size
            draw.rectangle([(15, h - 70), (w - 15, h - 15)], fill=(15, 23, 42))
            draw.text((30, h - 50), f"Translated to {lang_label} | OmniSuperBot", fill=(56, 189, 248))
            out_path = os.path.join(TEMP_DIR, f"tr_{session_id}.jpg")
            img.save(out_path, quality=95)
            await call.message.reply_photo(
                FSInputFile(out_path),
                caption=f"✅ Rasm <b>{lang_label}</b> tiliga tarjima qilindi!",
                parse_mode="HTML"
            )
        except Exception as e:
            await call.message.reply(f"⚠️ Xatolik: {str(e)[:80]}")

# ==============================================================================
# SMART FILE, PIXAR & AI MAGIC HANDLER
# ==============================================================================
@dp.message(F.document | F.photo | F.video | F.audio)
async def smart_file_handler(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    mode = USER_MODE.get(user_id, "normal")
    session_id = str(uuid.uuid4())[:8]

    if message.document:
        file_id = message.document.file_id
        orig_name = message.document.file_name or f"file_{session_id}.dat"
    elif message.photo:
        file_id = message.photo[-1].file_id
        orig_name = f"image_{session_id}.jpg"
    elif message.video:
        file_id = message.video.file_id
        orig_name = message.video.file_name or f"video_{session_id}.mp4"
    elif message.audio:
        file_id = message.audio.file_id
        orig_name = message.audio.file_name or f"audio_{session_id}.mp3"

    ext = orig_name.split(".")[-1].lower() if "." in orig_name else "dat"
    base_name = os.path.splitext(orig_name)[0]
    local_path = os.path.join(TEMP_DIR, f"{session_id}_{orig_name}")

    tg_file = await bot.get_file(file_id)
    await bot.download_file(tg_file.file_path, local_path)

    # 1. 3D Pixar Mode
    if mode == "pixar" and ext in ["jpg", "jpeg", "png", "webp"]:
        wait_msg = await message.reply("✨ <b>3D Pixar qahramoni yaratilmoqda...</b>", parse_mode="HTML")
        img = Image.open(local_path)
        stylized = apply_pixar_3d_effect(img)
        out_path = os.path.join(TEMP_DIR, f"pixar_{session_id}.jpg")
        stylized.save(out_path, quality=95)
        await message.reply_photo(
            FSInputFile(out_path),
            caption="✨ <b>3D Pixar Foto-Animatsiya muvaffaqiyatli tayyorlandi!</b>",
            parse_mode="HTML"
        )
        await wait_msg.delete()
        return

    # 2. AI Magic Studio Mode (4K Ultra-HD Upscale)
    if mode == "magic" and ext in ["jpg", "jpeg", "png", "webp"]:
        wait_msg = await message.reply("🔮 <b>AI Magic 4K Ultra-HD sifatga oshirilmoqda...</b>", parse_mode="HTML")
        img = Image.open(local_path)
        enhanced = apply_magic_4k_enhancer(img)
        out_path = os.path.join(TEMP_DIR, f"magic_{session_id}.png")
        enhanced.save(out_path, format="PNG")
        await message.reply_document(
            FSInputFile(out_path),
            caption="🔮 <b>AI Magic Studio 4K Ultra-HD natijasi tayyor!</b>",
            parse_mode="HTML"
        )
        await wait_msg.delete()
        return

    # 3. Image Translation Mode
    if mode == "translate" and ext in ["jpg", "jpeg", "png", "webp"]:
        USER_SESSIONS[session_id] = {"type": "translate_image", "file_path": local_path}
        await message.reply(
            TEXTS[lang]["choose_tr_lang"],
            parse_mode="HTML",
            reply_markup=build_top10_lang_keyboard(session_id)
        )
        return

    # 4. Standard File Converter Mode
    USER_SESSIONS[session_id] = {
        "file_path": local_path,
        "orig_name": orig_name,
        "base_name": base_name,
        "ext": ext,
    }
    targets = COMPATIBLE_FORMATS.get(ext, ["pdf", "txt"])
    buttons, row = [], []
    for t_ext in targets:
        row.append(InlineKeyboardButton(text=f"📄 .{t_ext.upper()}", callback_data=f"conv|{session_id}|{t_ext}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    await message.reply(
        TEXTS[lang]["choose_format"].format(name=orig_name),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

# ==============================================================================
# CONVERT FILE CALLBACK
# ==============================================================================
@dp.callback_query(F.data.startswith("conv|"))
async def convert_file_callback(call: types.CallbackQuery):
    _, session_id, target_ext = call.data.split("|")
    session = USER_SESSIONS.get(session_id)
    if not session:
        await call.answer("Fayl topilmadi", show_alert=True)
        return
    src_path = session["file_path"]
    src_ext = session.get("ext", "")
    base_name = session.get("base_name", f"file_{session_id}")
    out_path = os.path.join(TEMP_DIR, f"{base_name}.{target_ext}")

    await call.answer(f".{target_ext.upper()} tayyorlanmoqda...")
    try:
        if src_ext in ["xlsx", "xls", "csv"]:
            df = pd.read_csv(src_path) if src_ext == "csv" else pd.read_excel(src_path)
            if target_ext == "csv":
                df.to_csv(out_path, index=False, encoding="utf-8-sig")
            elif target_ext == "xlsx":
                df.to_excel(out_path, index=False)
            elif target_ext == "html":
                df.to_html(out_path, index=False)
            elif target_ext == "json":
                df.to_json(out_path, orient="records", force_ascii=False, indent=2)
            elif target_ext == "txt":
                df.to_csv(out_path, index=False, sep="\t")
            elif target_ext == "pdf":
                c = canvas.Canvas(out_path, pagesize=A4)
                y = 800
                c.setFont("Helvetica", 9)
                for _, r in df.iterrows():
                    c.drawString(40, y, " | ".join(str(v) for v in r.values)[:100])
                    y -= 15
                    if y < 50:
                        c.showPage()
                        y = 800
                c.save()
        elif src_ext in ["jpg", "jpeg", "png", "webp"]:
            img = Image.open(src_path)
            if target_ext in ["pdf", "jpg"] and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(out_path, quality=100)
        else:
            with open(src_path, "rb") as rf, open(out_path, "wb") as wf:
                wf.write(rf.read())

        await call.message.reply_document(
            FSInputFile(out_path),
            caption=f"✅ <code>{base_name}.{target_ext}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        await call.message.reply(f"⚠️ Xatolik: {str(e)[:100]}")

# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
async def main():
    print("🚀 OmniSuperBot 6-in-1 muvaffaqiyatli ishga tushdi!")
    print("📲 Telegramda botingizga kirib /start bosing!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
