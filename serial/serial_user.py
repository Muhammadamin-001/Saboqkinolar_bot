# serial/serial_user.py
"""
👤 SERIAL USER VIEW
Foydalanuvchi uchun serialni ko'rish, qismlar, playback
"""

from telebot import types
from utils.db_config import bot
from .serial_db import get_serial, get_season, get_episode
from utils.admin_utils import is_admin, user_panel, admin_panel
from config.settings import ADMIN_ID
kanal_link = "https://t.me/Saboq_kinolar"

# =================== FOYDALANUVCHI UCHUN SERIAL KO'RISH ===================

def show_serial_for_user(chat_id, serial_code):
    """✅ TUZATILGAN: Serialni ko'rsatish - season_number orqali"""

    serial = get_serial(serial_code)

    if not serial:
        bot.send_message(chat_id, "❌ Serial topilmadi!")
        return

    markup = types.InlineKeyboardMarkup()
    seasons = serial.get("seasons", [])

    if seasons:
        for idx, season in enumerate(seasons):
            season_num = season.get("season_number")
            season_name = season.get("season_name")

            # 🏷 Foydalanuvchiga ko'rinadigan nom
            if season_num:
                display = f"📺 {season_num}-fasl"
                # ✅ season_number jo'natamiz
                callback_id = str(season_num)
            else:
                display = f"📺 {season_name}"
                # ✅ season_name jo'natamiz (name_ prefix bilan)
                callback_id = f"name_{season_name}"

            markup.add(
                types.InlineKeyboardButton(
                    display,
                    callback_data=f"user_season_{serial_code}_{callback_id}"
                )
            )
    
    if hasattr(chat_id, "from_user"):
        user_id = chat_id.from_user.id
        target_chat_id = chat_id.chat.id
    else:
        user_id = chat_id
        target_chat_id = chat_id
    
    if (str(user_id) == str(ADMIN_ID) or is_admin(user_id)):        
        markup.add(
            types.InlineKeyboardButton("🎬 Kanalimiz", url=kanal_link),
            types.InlineKeyboardButton("🔙", callback_data="admin_back")
        )

    else:
        markup.add(
            types.InlineKeyboardButton("🎬 Kanalimiz", url=kanal_link),
            types.InlineKeyboardButton("🔙", callback_data="user_back")
        )

    caption = (
        f"🎞 *{serial['name']}*\n\n"
        f"🆔 Serial kodi: `{serial_code}`\n"
        f"{serial['description']}\n\n"
        f"Faslni tanlang:"
    )

    bot.send_photo(
        target_chat_id,
        serial["image"],
        caption=caption,
        parse_mode="Markdown",
        reply_markup=markup
    )


# =================== QISMLAR XABARI - ✅ TUZATILGAN ===================

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_season_"))
def show_episodes_for_user(call):
    """✅ TUZATILGAN: season_number yoki season_name orqali qidirish + pagination"""
    
    # ✅ TUZATILGAN: Pagination sahifasini aniq parseytlash
    if "_page_" in call.data:
        parts = call.data.split("_page_")
        page = int(parts[1])
        season_data = parts[0]  # user_season_CODE_SEASONID
        season_parts = season_data.split("_", 3)
    else:
        page = 0
        season_parts = call.data.split("_", 3)
    
    serial_code = season_parts[2]
    season_id = season_parts[3]  # season_number, name_xxxxx

    serial = get_serial(serial_code)
    if not serial:
        bot.answer_callback_query(call.id, "❌ Serial topilmadi!")
        return

    # ✅ TUZATILGAN: Season ID ni aniq parseytlash
    season = None
    season_display = ""
    
    if season_id.startswith("name_"):
        # Season name orqali qidirish
        season_name = season_id.replace("name_", "")
        seasons = serial.get("seasons", [])
        for s in seasons:
            if s.get("season_name") == season_name:
                season = s
                season_display = season_name
                break
    else:
        # Season number orqali qidirish
        try:
            season_num = int(season_id)
            season = get_season(serial_code, season_num)
            if season:
                season_display = f"{season_num}-fasl"
        except (ValueError, TypeError):
            season = None

    if not season:
        bot.answer_callback_query(call.id, "❌ Fasl topilmadi!")
        return

    bot.delete_message(call.message.chat.id, call.message.message_id)

    episodes = season.get("episodes", [])
    full_files = season.get("full_files", [])
    
    # ✅ TUZATILGAN: Qismlarni to'g'ri yaratish
    if episodes:
        total = episodes
    elif full_files:
        total = [{"episode_number": i+1} for i in range(len(full_files))]
    else:
        total = []

    PER_PAGE = 24
    PER_ROW = 4

    start = page * PER_PAGE
    end = start + PER_PAGE
    page_items = total[start:end]

    markup = types.InlineKeyboardMarkup()

    # 🔢 QISMLAR (4 tadan qatorda)
    row = []
    for item in page_items:
        ep_num = item.get("episode_number") if isinstance(item, dict) else item
        row.append(
            types.InlineKeyboardButton(
                str(ep_num),
                callback_data=f"user_episode_{serial_code}_{season_id}_{ep_num}"
            )
        )
        if len(row) == PER_ROW:
            markup.row(*row)
            row = []

    if row:
        markup.row(*row)

    # 🔁 PAGINATION - ✅ TUZATILGAN
    nav = []
    if page > 0:
        nav.append(
            types.InlineKeyboardButton(
                "⬅️ Oldingi",
                callback_data=f"user_season_{serial_code}_{season_id}_page_{page-1}"
            )
        )
    if end < len(total):
        nav.append(
            types.InlineKeyboardButton(
                "Keyingi ➡️",
                callback_data=f"user_season_{serial_code}_{season_id}_page_{page+1}"
            )
        )

    if nav:
        markup.row(*nav)

    # 🔙 ORTGA TUGMASI
    markup.add(
        types.InlineKeyboardButton(
            "🔙 Ortga",
            callback_data=f"user_view_serial_{serial_code}"
        )
    )

    # Qismlar menyu
    season_num = season.get("season_number", "")
    season_name = season.get("season_name", "")
    
    if season_num:
        display = f"{season_num}-fasl"
    else:
        display = season_name

    caption = (
        f"📺 *{serial['name']}*\n"
        f"🎬 *{display}*\n\n"
        f"Qismlarni tanlang:"
    )

    bot.send_message(
        call.message.chat.id,
        caption,
        reply_markup=markup,
        parse_mode="Markdown"
    )


# =================== QISMNI YUBORISH - ✅ TO'LIQ TUZATILGAN ===================

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_episode_"))
def send_episode_to_user(call):
    """✅ TO'LIQ TUZATILGAN: Qismni foydalanuvchiga yuborish (season_name bilan ham)"""
    
    try:
        # ✅ TUZATILGAN: Callback datani to'g'ri parseytlash
        callback_data = call.data.replace("user_episode_", "")
        
        # Oxirgi element episode_number (raqam)
        last_underscore = callback_data.rfind("_")
        episode_number = int(callback_data[last_underscore+1:])
        
        # Kalgan qismi serial_code_season_id
        remaining = callback_data[:last_underscore]
        
        # Season_id topish (name_ bilan bo'lsa, name_dan keyingi hamma)
        if "name_" in remaining:
            # name_ pozitsiyasini top
            name_index = remaining.find("name_")
            serial_code = remaining[:name_index].rstrip("_")
            season_id = remaining[name_index:]  # name_XXXXX
        else:
            # Raqam bo'lsa, oxirgi underscore oldingi raqam
            parts = remaining.split("_")
            season_id = parts[-1]  # oxirgi element season_number
            serial_code = "_".join(parts[:-1])  # qolgan qismi serial_code

        print(f"DEBUG: serial_code='{serial_code}', season_id='{season_id}', episode_number={episode_number}")

    except Exception as e:
        print(f"❌ Callback data parseytlash xatosi: {e}")
        bot.answer_callback_query(call.id, f"❌ Xato: {str(e)}")
        return

    serial = get_serial(serial_code)
    if not serial:
        print(f"❌ Serial topilmadi: {serial_code}")
        bot.answer_callback_query(call.id, "❌ Serial topilmadi!")
        return

    print(f"✅ Serial topildi: {serial.get('name')}")

    # ✅ TUZATILGAN: Season ni aniq topish
    season = None
    season_display = ""
    
    if season_id.startswith("name_"):
        season_name = season_id.replace("name_", "", 1)  # Faqat birinchi name_ almashtir
        print(f"DEBUG: Season name orqali qidirish: '{season_name}'")
        
        for s in serial.get("seasons", []):
            if s.get("season_name") == season_name:
                season = s
                season_display = season_name
                print(f"✅ Season topildi (name): {season_name}")
                break
    else:
        try:
            season_num = int(season_id)
            print(f"DEBUG: Season number orqali qidirish: {season_num}")
            
            season = get_season(serial_code, season_num)
            if season:
                season_display = f"{season_num}-fasl"
                print(f"✅ Season topildi (number): {season_num}")
        except (ValueError, TypeError) as e:
            print(f"❌ Season number parseytlash xatosi: {e}")
            season = None

    if not season:
        print(f"❌ Fasl topilmadi: season_id={season_id}")
        bot.answer_callback_query(call.id, "❌ Fasl topilmadi!")
        return

    print(f"✅ Season ma'lumotlari: {season}")

    # ✅ TUZATILGAN: Qismni aniq topish
    episode = None
    episodes_list = season.get("episodes", [])
    print(f"DEBUG: Mavjud qismlar: {[ep.get('episode_number') for ep in episodes_list]}")
    
    for ep in episodes_list:
        if ep.get("episode_number") == episode_number:
            episode = ep
            print(f"✅ Qism topildi: {episode_number}")
            break

    if not episode:
        print(f"❌ Qism topilmadi: {episode_number}")
        bot.answer_callback_query(call.id, "❌ Qism topilmadi!")
        return

    file_id = episode.get("file_id")
    if file_id:
        try:
            print(f"📹 Video yuborilmoqda: file_id={file_id[:20]}...")
            bot.send_video(
                call.message.chat.id,
                file_id,
                caption=f"📺 *{serial['name']}*\n🎬 *{season_display}*\n🎞️ *Qism {episode_number}*",
                parse_mode="Markdown"
            )
            bot.answer_callback_query(call.id, "✅ Video jo'natildi!")
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ Xato: {str(e)[:50]}")
            print(f"❌ Video yuborish xatosi: {e}")
    else:
        print("❌ File ID topilmadi")
        bot.answer_callback_query(call.id, "❌ Video topilmadi!")

# =================== ORTGA TUGMALARI ===================

@bot.callback_query_handler(func=lambda call: call.data == "user_back")
def user_back_to_home(call):
    """Seriallardan asosiy menyuga qaytish"""
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    markup = user_panel()
    bot.send_message(
        call.message.chat.id,
        "👤 *Asosiy Panel*",
        reply_markup=markup,
        parse_mode="Markdown"
    )
@bot.callback_query_handler(func=lambda call: call.data == "admin_back")
def admin_back_to_home(call):
    """Seriallardan asosiy menyuga qaytish"""
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    markup = admin_panel()
    bot.answer_callback_query(
        call.id,
        "👤 *Asosiy Panel*",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_view_serial_"))
def user_view_serial(call):
    """✅ TUZATILGAN: Foydalanuvchi serialni ko'rish"""
    serial_code = call.data.replace("user_view_serial_", "")
    
    if not serial_code:  # ✅ Bo'sh code tekshiruvi
        bot.answer_callback_query(call.id, "❌ Serial topilmadi!")
        return
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    show_serial_for_user(call.message.chat.id, serial_code)


@bot.callback_query_handler(func=lambda call: call.data == "user_back_from_serials")
def user_back_from_serials(call):
    """Seriallar ro'yxatidan asosiy menyuga qaytish"""
    bot.delete_message(call.message.chat.id, call.message.message_id)
    from utils.admin_utils import user_panel
    markup = user_panel()
    bot.send_message(
        call.message.chat.id,
        "👤 *Asosiy Panel*",
        reply_markup=markup,
        parse_mode="Markdown"
    
    
    )