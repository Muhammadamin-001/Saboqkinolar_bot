"""
💰 USER DONAT PANELI
Foydalanuvchi uchun karta ko'rish
"""

from telebot import types
from utils.db_config import bot, cards_collection

# =================== USER DONAT TUGMASI ===================

@bot.callback_query_handler(func=lambda call: call.data == "🎁 Donat")
def user_donate_menu(call):
    """Foydalanuvchi donat kartasini ko'rish"""
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    # Bazadan barcha kartalarni olish
    cards = list(cards_collection.find({}, {"_id": 0, "type": 1, "number": 1, "owner": 1}))
    
    if not cards:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Ortga", callback_data="user_back"))
        bot.send_message(
            call.message.chat.id,
            "❌ *Hozir donate kartasi yo'q*",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return
    
    markup = types.InlineKeyboardMarkup()
    
    for idx, card in enumerate(cards):
        display = f"{card['type']}"
        markup.add(
            types.InlineKeyboardButton(
                display,
                callback_data=f"user_donate_card_{idx}"
            )
        )
    
    markup.add(types.InlineKeyboardButton("❌", callback_data="user_donate_delete"))
    
    bot.send_message(
        call.message.chat.id,
        "💰 *Donat uchun karta tanlang:*",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_donate_card_"))
def user_donate_card_show(call):
    """Karta ma'lumotlarini ko'rsatish"""
    try:
        idx = int(call.data.replace("user_donate_card_", ""))
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
    markup.add(types.InlineKeyboardButton("❌", callback_data="user_donate_delete"))
    
    bot.send_message(
        call.message.chat.id,
        f"💰 *Donat Karta*\n\n"
        f"🔖 Turi: `{card['type']}`\n"
        f"💳 Raqami: `{card['number']}`\n"
        f"👤 Egasi: {card['owner']}",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "user_donate_delete")
def user_donate_delete(call):
    """Xabarni o'chirish"""
    bot.delete_message(call.message.chat.id, call.message.message_id)