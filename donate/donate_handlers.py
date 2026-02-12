"""
💳 SUPER ADMIN KARTA BOSHQARUVI
Super Admin uchun "Add Card" menyu
"""

import time
from telebot import types
from utils.db_config import bot, cards_collection, state
from config.settings import ADMIN_ID

# =================== SUPER ADMIN "Add Card" TUGMASI ===================

@bot.message_handler(func=lambda msg: msg.text == "💳 Add Card")
def add_card_menu_super_admin(msg):
    """💳 Karta paneli menyu (Super Admin uchun)"""
    user_id = str(msg.from_user.id)
    
    # ✅ SUPER ADMIN TEKSHIRUVI
    if user_id != str(ADMIN_ID):
        bot.send_message(msg.chat.id, "❌ Ruxsat yo'q!")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("➕ Karta qo'shish", callback_data="card_add"),
        types.InlineKeyboardButton("❌ Karta o'chirish", callback_data="card_delete_menu")
    )
    markup.add(types.InlineKeyboardButton("🔙 Ortga", callback_data="admin_back_to_panel"))
    
    bot.send_message(
        msg.chat.id,
        "💳 *Karta Paneli*\n\nQanday amal bajarasiz?",
        reply_markup=markup,
        parse_mode="Markdown"
    )


# =================== KARTA QO'SHISH ===================

@bot.callback_query_handler(func=lambda call: call.data == "card_add")
def card_add_start(call):
    """Karta qo'shishni boshlash"""
    user_id = str(call.from_user.id)
    
    if user_id != str(ADMIN_ID):
        bot.answer_callback_query(call.id, "❌ Ruxsat yo'q!")
        return
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⛔️ Bekor", callback_data="add_card_cancel"))
    
    bot.send_message(
        call.message.chat.id,
        "🆔 *Karta turini kiriting*\n\n(Masalan: UZCARD, HUMO, VISA, MasterCard)",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    state[user_id] = ["waiting_card_type"]

@bot.message_handler(func=lambda msg: str(msg.from_user.id) in state 
                     and state[str(msg.from_user.id)][0] == "waiting_card_type")
def card_type_handler(msg):
    """Karta turini qabul qilish"""
    user_id = str(msg.from_user.id)
    card_type = msg.text.strip().upper()
    
    if not card_type or len(card_type) < 3:
        bot.send_message(msg.chat.id, "❌ Karta turi kamina 3 ta belgi bo'lishi kerak!")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⛔️ Bekor", callback_data="add_card_cancel"))
    
    bot.send_message(
        msg.chat.id,
        "💳 *Karta raqamini kiriting*\n\n(Masalan: 8600 1234 5678 2345)",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    state[user_id] = ["waiting_card_number", card_type]

@bot.message_handler(func=lambda msg: str(msg.from_user.id) in state 
                     and state[str(msg.from_user.id)][0] == "waiting_card_number")
def card_number_handler(msg):
    """Karta raqamini qabul qilish"""
    user_id = str(msg.from_user.id)
    card_type = state[user_id][1]
    card_number = msg.text.strip()
    
    # Raqam tekshiruvi
    digits_only = card_number.replace(" ", "")
    if not digits_only.isdigit() or len(digits_only) < 13 or len(digits_only) > 19:
        bot.send_message(msg.chat.id, "❌ Karta raqami noto'g'ri! Qayta kiriting:")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⛔️ Bekor", callback_data="add_card_cancel"))
    
    bot.send_message(
        msg.chat.id,
        "👤 *Karta egasining ism-sharifini kiriting*\n\n(Masalan: Alisher Aliyev)",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    state[user_id] = ["waiting_card_owner", card_type, card_number]

@bot.message_handler(func=lambda msg: str(msg.from_user.id) in state 
                     and state[str(msg.from_user.id)][0] == "waiting_card_owner")
def card_owner_handler(msg):
    """Karta egasini qabul qilish va bazaga saqlash"""
    user_id = str(msg.from_user.id)
    card_type = state[user_id][1]
    card_number = state[user_id][2]
    card_owner = msg.text.strip()
    
    if not card_owner or len(card_owner) < 3:
        bot.send_message(msg.chat.id, "❌ Ism kamina 3 ta belgi bo'lishi kerak!")
        return
    
    # ✅ MONGODB ATLASGA SAQLASH
    cards_collection.insert_one({
        "type": card_type,
        "number": card_number,
        "owner": card_owner,
        "added_by": user_id,
        "added_time": time.time()
    })
    
    bot.send_message(
        msg.chat.id,
        f"✅ *Karta ma'lumotlari saqlandi!*\n\n"
        f"🔖 Turi: `{card_type}`\n"
        f"💳 Raqami: `{card_number}`\n"
        f"👤 Egasi: {card_owner}",
        parse_mode="Markdown"
    )
    
    print(f"✅ Karta qo'shildi: {card_type} - {card_number}")
    del state[user_id]

# =================== KARTA O'CHIRISH ===================

@bot.callback_query_handler(func=lambda call: call.data == "card_delete_menu")
def card_delete_menu(call):
    """Karta o'chirish menyusi"""
    user_id = str(call.from_user.id)
    
    if user_id != str(ADMIN_ID):
        bot.answer_callback_query(call.id, "❌ Ruxsat yo'q!")
        return
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    # Bazadan barcha kartalarni olish
    cards = list(cards_collection.find({}, {"_id": 0, "type": 1, "number": 1, "owner": 1}))
    
    if not cards:
        bot.send_message(
            call.message.chat.id,
            "❌ *Bazaga karta qo'shilmagan*",
            parse_mode="Markdown"
        )
        return
    
    markup = types.InlineKeyboardMarkup()
    
    for idx, card in enumerate(cards):
        display = f"💳 {card['type']} - {card['number'][-4:]} ({card['owner']})"
        markup.add(
            types.InlineKeyboardButton(
                display,
                callback_data=f"delete_card_select_{idx}"
            )
        )
    
    markup.add(types.InlineKeyboardButton("🔙 Ortga", callback_data="add_card_menu_super_admin"))
    
    bot.send_message(
        call.message.chat.id,
        "🗑️ *O'chirmoqchi bo'lgan kartani tanlang:*",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_card_select_"))
def delete_card_select(call):
    """Karta tanlandi, tasdiqlash"""
    user_id = str(call.from_user.id)
    
    if user_id != str(ADMIN_ID):
        bot.answer_callback_query(call.id, "❌ Ruxsat yo'q!")
        return
    
    try:
        idx = int(call.data.replace("delete_card_select_", ""))
    except:
        bot.answer_callback_query(call.id, "❌ Xatolik!")
        return
    
    # Bazadan kartani olish
    cards = list(cards_collection.find({}, {"_id": 0, "type": 1, "number": 1, "owner": 1}))
    
    if idx >= len(cards):
        bot.answer_callback_query(call.id, "❌ Karta topilmadi!")
        return
    
    card = cards[idx]
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Ha, o'chiraman", callback_data=f"delete_card_confirm_{idx}"),
        types.InlineKeyboardButton("❌ Yo'q, bekor", callback_data="card_delete_menu")
    )
    
    bot.send_message(
        call.message.chat.id,
        f"⚠️ *Karta ma'lumotlari:*\n\n"
        f"🔖 Turi: `{card['type']}`\n"
        f"💳 Raqami: `{card['number']}`\n"
        f"👤 Egasi: {card['owner']}\n\n"
        f"Aniq o'chirmoqchisiz?",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_card_confirm_"))
def delete_card_confirm(call):
    """Karta o'chirish tasdiqi"""
    user_id = str(call.from_user.id)
    
    if user_id != str(ADMIN_ID):
        bot.answer_callback_query(call.id, "❌ Ruxsat yo'q!")
        return
    
    try:
        idx = int(call.data.replace("delete_card_confirm_", ""))
    except:
        bot.answer_callback_query(call.id, "❌ Xatolik!")
        return
    
    # Kartani topish va o'chirish
    cards = list(cards_collection.find({}, {"_id": 0, "type": 1, "number": 1, "owner": 1}))
    
    if idx >= len(cards):
        bot.answer_callback_query(call.id, "❌ Karta topilmadi!")
        return
    
    card = cards[idx]
    
    # MongoDB'dan o'chirish
    result = cards_collection.delete_one({
        "type": card['type'],
        "number": card['number'],
        "owner": card['owner']
    })
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    if result.deleted_count > 0:
        bot.send_message(
            call.message.chat.id,
            f"✅ *Karta o'chirildi!*\n\n"
            f"🔖 {card['type']} - {card['number'][-4:]}",
            parse_mode="Markdown"
        )
        print(f"✅ Karta o'chirildi: {card['type']}")
    else:
        bot.send_message(
            call.message.chat.id,
            "❌ *O'chirishda xatolik yuz berdi!*",
            parse_mode="Markdown"
        )

# =================== BEKOR QILISH TUGMALARI ===================

@bot.callback_query_handler(func=lambda call: call.data == "add_card_cancel")
def add_card_cancel(call):
    """Karta qo'shishni bekor qilish"""
    user_id = str(call.from_user.id)
    
    if user_id in state:
        del state[user_id]
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("➕ Karta qo'shish", callback_data="card_add"),
        types.InlineKeyboardButton("❌ Karta o'chirish", callback_data="card_delete_menu")
    )
    markup.add(types.InlineKeyboardButton("🔙 Ortga", callback_data="admin_back_to_panel"))
    
    bot.send_message(
        call.message.chat.id,
        "💳 *Karta Paneli*\n\nQanday amal bajarasiz?",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "add_card_menu_super_admin")
def add_card_menu_callback(call):
    """Callback orqali karta paneliga qaytish"""
    bot.delete_message(call.message.chat.id, call.message.message_id)
    add_card_menu_super_admin(call.message)

# =================== ORTGA TUGMASI ===================

@bot.callback_query_handler(func=lambda call: call.data == "admin_back_to_panel")
def admin_back_to_panel(call):
    """Super Admin paneliga qaytish"""
    bot.delete_message(call.message.chat.id, call.message.message_id)
    from utils.admin_utils import super_admin_panel
    super_admin_panel(call.message.chat.id)