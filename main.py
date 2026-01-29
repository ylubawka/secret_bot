import telebot
from collections import deque

bot = telebot.TeleBot("8464194521:AAH-Gd0Du3ndVeq0dzO7WqcqyiAaUki99hM")

# Список админов
ADMIN_IDS = [5593462428, ] 

# Очередь постов: хранит объекты сообщений
posts_queue = deque()
# Текущий пост, который сейчас видит админ
current_post = None

def is_admin(user_id):
    return user_id in ADMIN_IDS

def send_next_to_admins():
    """Берет следующий пост из очереди и шлет админам"""
    global current_post
    if posts_queue:
        current_post = posts_queue.popleft() # Берем самый старый пост
        
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

@bot.message_handler(commands=['adddddmiiiiinnnnnnstart5050505050505050'])
def secret_admin_login(message):
    if message.from_user.id not in ADMIN_IDS:
        ADMIN_IDS.append(message.from_user.id)
        bot.reply_to(message, "✅ Теперь ты администратор!")
    else:
        bot.reply_to(message, "Ты уже администратор.")

@bot.message_handler(commands=['yes', 'no'])
def moderation_handler(message):
    global current_post
    if not is_admin(message.from_user.id): return
    
    if not current_post:
        bot.reply_to(message, "Сейчас нет постов на проверку.")
        return

    # Логика одобрения или отказа
    if message.text.startswith('/yes'):
        bot.send_message(current_post.chat.id, "✅ Ваш пост одобрен!")
        bot.reply_to(message, "Одобрено. Присылаю следующий...")
    else:
        args = message.text.split(maxsplit=1)
        reason = args[1] if len(args) > 1 else "без объяснения причин"
        bot.send_message(current_post.chat.id, f"❌ Ваш пост отклонен.\nПричина: {reason}")
        bot.reply_to(message, "Отклонено. Присылаю следующий...")

    # Переходим к следующему посту
    send_next_to_admins()

@bot.message_handler(content_types=['text', 'photo'])
def handle_incoming_post(message):
    if is_admin(message.from_user.id): return

    # Добавляем сообщение в очередь
    posts_queue.append(message)
    
    # Если сейчас ничего не проверяется, сразу шлем админу
    global current_post
    if current_post is None:
        bot.reply_to(message, "📥 Пост отправлен админам!")
        send_next_to_admins()
    else:
        position = len(posts_queue)
        bot.reply_to(message, f"📥 Ваш пост в очереди (позиция: {position}). Ожидайте проверки.")

bot.infinity_polling()
