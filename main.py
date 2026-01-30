import telebot
from collections import deque

# Замени токен на свой. Не забудь добавить бота в админы канала!
bot = telebot.TeleBot("8464194521:AAH-Gd0Du3ndVeq0dzO7WqcqyiAaUki99hM")

ADMIN_IDS = [5593462428] 
BANNED_IDS = set() # Список забаненных (в памяти, сбросится при перезапуске)
CHANNEL_ID = "@твой_канал" # ID канала (например, @my_channel или -100...)

posts_queue = deque()
current_post = None

def is_admin(user_id):
    return user_id in ADMIN_IDS

def send_next_to_admins():
    global current_post
    if posts_queue:
        current_post = posts_queue.popleft()
        username = f"@{current_post.from_user.username}" if current_post.from_user.username else "Без ника"
        info = f"🔔 Новый пост от {username} (ID: {current_post.from_user.id}):\n\n"

        for admin_id in ADMIN_IDS:
            try:
                if current_post.content_type == 'text':
                    bot.send_message(admin_id, info + current_post.text)
                elif current_post.content_type == 'photo':
                    caption = current_post.caption if current_post.caption else ""
                    bot.send_photo(admin_id, current_post.photo[-1].file_id, caption=info + caption)
            except Exception as e:
                print(f"Ошибка отправки админу {admin_id}: {e}")
    else:
        current_post = None
        for admin_id in ADMIN_IDS:
            bot.send_message(admin_id, "✅ Все посты проверены. Очередь пуста!")

@bot.message_handler(commands=['start', 'myid'])
def start_handler(message):
    if message.text == '/myid':
        bot.reply_to(message, f"Твой ID: `{message.from_user.id}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "Отправь пост, и он попадет в очередь на модерацию.")

# --- БЛОК АДМИН-КОМАНД ---

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        user_id = int(args[1])
        BANNED_IDS.add(user_id)
        bot.reply_to(message, f"🚫 Пользователь {user_id} заблокирован.")
    else:
        bot.reply_to(message, "Используй: /ban [ID]")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        user_id = int(args[1])
        BANNED_IDS.discard(user_id)
        bot.reply_to(message, f"✅ Пользователь {user_id} разблокирован.")
    else:
        bot.reply_to(message, "Используй: /unban [ID]")

@bot.message_handler(commands=['yes', 'no'])
def moderation_handler(message):
    global current_post
    if not is_admin(message.from_user.id): return
    
    if not current_post:
        bot.reply_to(message, "Сейчас нет постов на проверку.")
        return

    if message.text.startswith('/yes'):
        # Публикация в канал
        try:
            if current_post.content_type == 'text':
                bot.send_message(CHANNEL_ID, current_post.text)
            elif current_post.content_type == 'photo':
                bot.send_photo(CHANNEL_ID, current_post.photo[-1].file_id, caption=current_post.caption)
            
            bot.send_message(current_post.chat.id, "✅ Ваш пост одобрен и опубликован!")
            bot.reply_to(message, "Опубликовано в канал. Присылаю следующий...")
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка публикации: {e}")
    else:
        args = message.text.split(maxsplit=1)
        reason = args[1] if len(args) > 1 else "без объяснения причин"
        bot.send_message(current_post.chat.id, f"❌ Ваш пост отклонен.\nПричина: {reason}")
        bot.reply_to(message, "Отклонено. Присылаю следующий...")

    send_next_to_admins()

# --- ОБРАБОТКА ВХОДЯЩИХ ПОСТОВ ---

@bot.message_handler(content_types=['text', 'photo'])
def handle_incoming_post(message):
    if is_admin(message.from_user.id): return
    
    # Проверка на бан
    if message.from_user.id in BANNED_IDS:
        bot.reply_to(message, "⛔ Вы заблокированы и не можете отправлять посты.")
        return

    posts_queue.append(message)
    
    global current_post
    if current_post is None:
        bot.reply_to(message, "📥 Пост отправлен админам!")
        send_next_to_admins()
    else:
        position = len(posts_queue)
        bot.reply_to(message, f"📥 Ваш пост в очереди (позиция: {position}). Ожидайте проверки.")

bot.infinity_polling()
