# serial/serial_user.py
"""
👤 SERIAL USER VIEW
Foydalanuvchi uchun serialni ko'rish, qismlar, playback
"""

from telebot import types
from utils.db_config import bot
from .serial_db import get_serial, get_season, get_episode

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
                # ✅ TUZATILGAN: season_num jo'natamiz, idx emas
                callback_id = season_num
            else:
                display = f"📺 {season_name}"
                # Agar raqam bo'lmasa, season_name orqali qidirish uchun special ID
                callback_id = f"name_{season_name}"

            markup.add(
                types.InlineKeyboardButton(
                    display,
                    callback_data=f"user_season_{serial_code}_{callback_id}"
                )
            )

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
        chat_id,
        serial["image"],
        caption=caption,
        parse_mode="Markdown",
        reply_markup=markup
    )


# =================== QISMLAR XABARI ===================

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_season_"))
def show_episodes_for_user(call):
    """✅ TUZATILGAN: season_number yoki season_name orqali qidirish"""
    parts = call.data.split("_", 3)  # 3 qismga bo'lish
    serial_code = parts[2]
    season_id = parts[3]  # Bu season_number yoki name_xxxxx bo'lishi mumkin
    page = int(call.data.split("_page_")[-1]) if "_page_" in call.data else 0

    serial = get_serial(serial_code)
    if not serial:
        bot.answer_callback_query(call.id, "❌ Serial topilmadi!")
        return

    # ✅ TUZATILGAN: Season ID ni parseytlash
    season = None
    if season_id.startswith("name_"):
        # Season name orqali qidirish
        season_name = season_id.replace("name_", "")
        seasons = serial.get("seasons", [])
        for s in seasons:
            if s.get("season_name") == season_name:
                season = s
                break
    else:
        # Season number orqali qidirish
        try:
            season_num = int(season_id)
            season = get_season(serial_code, season_num)
        except ValueError:
            season = None

    if not season:
        bot.answer_callback_query(call.id, "❌ Fasl topilmadi!")
        return

    bot.delete_message(call.message.chat.id, call.message.message_id)

    episodes = season.get("episodes", [])
    full_files = season.get("full_files", [])
    total = episodes or list(range(1, len(full_files) + 1))

    PER_PAGE = 24
    PER_ROW = 4

    start = page * PER_PAGE
    end = start + PER_PAGE
    page_items = total[start:end]

    markup = types.InlineKeyboardMarkup()

    # 🔢 QISMLAR (4 tadan qatorda)
    row = []
    for item in page_items:
        ep_num = item["episode_number"] if isinstance(item, dict) else item
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

    # 🔁 PAGINATION
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
    season_display = f"{season_num}-fasl" if season_num else season_name

    caption = (
        f"📺 *{serial['name']}*\n"
        f"🎬 *{season_display}*\n\n"
        f"Qismlarni tanlang:"
    )

    bot.send_message(
        call.message.chat.id,
        caption,
        reply_markup=markup,
        parse_mode="Markdown"
    )


# =================== QISMNI YUBORISH ===================

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_episode_"))
def send_episode_to_user(call):
    """✅ TUZATILGAN: Qismni foydalanuvchiga yuborish"""
    parts = call.data.split("_", 4)  # 4 qismga bo'lish
    serial_code = parts[2]
    season_id = parts[3]  # season_number yoki name_xxxxx
    episode_number = int(parts[4])

    serial = get_serial(serial_code)
    if not serial:
        bot.answer_callback_query(call.id, "❌ Serial topilmadi!")
        return

    # ✅ TUZATILGAN: Season ni topish
    season = None
    if season_id.startswith("name_"):
        season_name = season_id.replace("name_", "")
        for s in serial.get("seasons", []):
            if s.get("season_name") == season_name:
                season = s
                break
    else:
        try:
            season_num = int(season_id)
            season = get_season(serial_code, season_num)
        except ValueError:
            season = None

    if not season:
        bot.answer_callback_query(call.id, "❌ Fasl topilmadi!")
        return

    # Qismni topish
    episode = None
    for ep in season.get("episodes", []):
        if ep["episode_number"] == episode_number:
            episode = ep
            break

    if not episode:
        bot.answer_callback_query(call.id, "❌ Qism topilmadi!")
        return

    file_id = episode.get("file_id")
    if file_id:
        try:
            bot.send_video(
                call.message.chat.id,
                file_id,
                caption=f"📺 {serial['name']} - Fasl {season_id}, Qism {episode_number}",
                parse_mode="Markdown"
            )
            bot.answer_callback_query(call.id, "✅ Video jo'natilmoqda...")
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ Xato: {str(e)[:50]}")
            print(f"    Video yuborish xatosi: {e}")
    else:
        bot.answer_callback_query(call.id, "❌ Video topilmadi!")


# =================== ORTGA TUGMALARI ===================

@bot.callback_query_handler(func=lambda call: call.data == "user_back")
def user_back_to_home(call):
    """Seriallardan asosiy menyuga qaytish"""
    bot.delete_message(call.message.chat.id, call.message.message_id)
    from utils.admin_utils import user_panel
    markup = user_panel()
    bot.send_message(
        call.message.chat.id,
        "👤 *Foydalanuvchi Paneli*",
        reply_markup=markup,
        parse_mode="Markdown"
    )


@bot.callback_query_handler(func=lambda call: call.data == "user_view_serial_" or call.data.startswith("user_view_serial_"))
def user_view_serial(call):
    """✅ TUZATILGAN: Foydalanuvchi serialni ko'rish"""
    serial_code = call.data.replace("user_view_serial_", "")
    
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
        "👤 *Foydalanuvchi Paneli*",
        reply_markup=markup,
        parse_mode="Markdown"
    )