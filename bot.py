import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ================ Налаштування ===================
# Вставте свій токен бота нижче
BOT_TOKEN = "7983993765:AAGu-NrdifmWMi_HlMVIZMvkwS8tpiJxXVU"

# Введіть ID адміністраторів через кому, наприклад:
ADMINS = {569585062,797671005} 
# ================================================

# Налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Глобальні змінні для зберігання даних
# Словник співробітників: ключ – ID користувача, значення – dict з "bonus" та "username"
employees = {}  
# Використовуємо список адміністраторів з налаштувань
admins = ADMINS

# Константи для станів розмови (ConversationHandler) в адмінпанелі
(ADMIN_MAIN, ADMIN_AWARD_SELECT, ADMIN_AWARD_ENTER, ADMIN_ADD, ADMIN_REMOVE) = range(5)


# ----- Обробник для команди /start -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Якщо користувач є адміністратором, показуємо адмінпанель
    if user_id in admins:
        text = "Вітаємо, адміністратор! Обери, що бажаєш зробити:"
        keyboard = [
            [InlineKeyboardButton("Нарахування бонусів", callback_data="admin_award")],
            [InlineKeyboardButton("Додати співробітника", callback_data="admin_add")],
            [InlineKeyboardButton("Видалити співробітника", callback_data="admin_remove")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)

    # Якщо користувач є співробітником, показуємо меню бонусів
    elif user_id in employees:
        bonus = employees[user_id]["bonus"]
        text = f"Привіт, хочешь подивитись бонуси?\nУ тебе {bonus} бонусів."
        keyboard = [[InlineKeyboardButton("Мої бонуси", callback_data="show_bonus")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text("Вибач, але ти не маєш доступу до цього бота.")


# ----- CallbackQueryHandler для обробки натискань кнопок -----
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    # Обробка кнопок для співробітників
    if data == "show_bonus":
        bonus = employees.get(user_id, {}).get("bonus", 0)
        text = f"Твої бонуси: {bonus}\nНатисни 'Назад' щоб повернутись."
        keyboard = [[InlineKeyboardButton("Назад", callback_data="back_employee")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)

    elif data == "back_employee":
        bonus = employees.get(user_id, {}).get("bonus", 0)
        text = f"Привіт, хочешь подивитись бонуси?\nУ тебе {bonus} бонусів."
        keyboard = [[InlineKeyboardButton("Мої бонуси", callback_data="show_bonus")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)

    # Обробка кнопок для адміністраторів
    elif data == "admin_award":
        # Якщо співробітників немає, повідомляємо про це
        if not employees:
            await query.edit_message_text("Немає співробітників. Додай спочатку співробітника.")
            return ADMIN_MAIN
        text = "Виберіть співробітника для нарахування бонусів:"
        keyboard = []
        # Створюємо кнопку для кожного співробітника (ID та нікнейм)
        for emp_id in employees.keys():
            username = employees[emp_id]["username"]
            button_text = f"{emp_id} - {username}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"award_{emp_id}")])
        keyboard.append([InlineKeyboardButton("Назад", callback_data="admin_back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)
        return ADMIN_AWARD_SELECT

    elif data.startswith("award_"):
        # Отримуємо ID вибраного співробітника
        selected_id = int(data.split("_")[1])
        context.user_data["selected_employee"] = selected_id
        text = (
            f"Введіть кількість бонусів для співробітника {selected_id} "
            f"(введіть 0 для скидання бонусів):"
        )
        keyboard = [[InlineKeyboardButton("Назад", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)
        return ADMIN_AWARD_ENTER

    elif data == "admin_add":
        text = "Введіть ID співробітника, якого потрібно додати:"
        keyboard = [[InlineKeyboardButton("Назад", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)
        return ADMIN_ADD

    elif data == "admin_remove":
        text = "Введіть ID співробітника, якого потрібно видалити:"
        keyboard = [[InlineKeyboardButton("Назад", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)
        return ADMIN_REMOVE

    elif data == "admin_back":
        # Повертаємося до головного меню адмінпанелі
        text = "Адмін панель:\nОбери дію:"
        keyboard = [
            [InlineKeyboardButton("Нарахування бонусів", callback_data="admin_award")],
            [InlineKeyboardButton("Додати співробітника", callback_data="admin_add")],
            [InlineKeyboardButton("Видалити співробітника", callback_data="admin_remove")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)
        return ADMIN_MAIN

    # Якщо натиснуто кнопку, яка не входить у поточну логіку
    return ConversationHandler.END


# ----- Обробник введення бонусів (адмін: нарахування бонусів) -----
async def admin_award_enter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    try:
        bonus_amount = int(user_input)
    except ValueError:
        await update.message.reply_text("Будь ласка, введіть коректне число.")
        return ADMIN_AWARD_ENTER

    selected_employee = context.user_data.get("selected_employee")
    if selected_employee is None:
        await update.message.reply_text("Не вибрано співробітника. Спробуйте ще раз.")
        return ADMIN_MAIN

    # Оновлюємо кількість бонусів для співробітника
    employees[selected_employee]["bonus"] = bonus_amount

    # Спробуємо повідомити співробітника (якщо бот може відправити повідомлення)
    try:
        await context.bot.send_message(
            chat_id=selected_employee,
            text=f"Вам нараховано {bonus_amount} бонусів!!",
        )
    except Exception as e:
        logging.error(f"Не вдалося повідомити співробітника {selected_employee}: {e}")

    await update.message.reply_text(
        f"Бонуси для співробітника {selected_employee} оновлено до {bonus_amount}.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="admin_back")]]),
    )
    return ADMIN_MAIN


# ----- Обробник введення ID для додавання співробітника -----
async def admin_add_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    try:
        new_emp_id = int(user_input)
    except ValueError:
        await update.message.reply_text("Будь ласка, введіть коректний ID (число).")
        return ADMIN_ADD

    if new_emp_id in employees:
        await update.message.reply_text("Співробітник з цим ID вже існує.")
    else:
        # Спробуємо отримати інформацію про користувача
        try:
            chat = await context.bot.get_chat(new_emp_id)
            # Якщо username відсутній, використовуємо first_name
            username = chat.username if chat.username else chat.first_name
        except Exception as e:
            logging.error(f"Не вдалося отримати інформацію для {new_emp_id}: {e}")
            username = "Unknown"
        employees[new_emp_id] = {"bonus": 0, "username": username}
        await update.message.reply_text(f"Новий працівник додан! {new_emp_id} - {username}")
    return ADMIN_MAIN


# ----- Обробник введення ID для видалення співробітника -----
async def admin_remove_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    try:
        rem_emp_id = int(user_input)
    except ValueError:
        await update.message.reply_text("Будь ласка, введіть коректний ID (число).")
        return ADMIN_REMOVE

    if rem_emp_id in employees:
        del employees[rem_emp_id]
        await update.message.reply_text("Співробітник видалений!")
    else:
        await update.message.reply_text("Співробітник з цим ID не знайдений.")
    return ADMIN_MAIN


# ----- Обробник команди /cancel для скасування розмови -----
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операцію скасовано.")
    return ConversationHandler.END


# ----- Основна функція запуску бота -----
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Обробник команди /start для всіх користувачів
    application.add_handler(CommandHandler("start", start))

    # ConversationHandler для адмінпанелі (нарахування бонусів, додавання та видалення співробітників)
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_handler, pattern="^(admin_award|admin_add|admin_remove)$")
        ],
        states={
            ADMIN_MAIN: [CallbackQueryHandler(button_handler, pattern="^admin_back$")],
            ADMIN_AWARD_SELECT: [CallbackQueryHandler(button_handler, pattern="^award_")],
            ADMIN_AWARD_ENTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_award_enter)],
            ADMIN_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_employee)],
            ADMIN_REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_remove_employee)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    application.add_handler(conv_handler)

    # Додатковий CallbackQueryHandler для обробки інших кнопок (наприклад, для співробітників)
    application.add_handler(CallbackQueryHandler(button_handler))

    # Запуск бота (long polling)
    application.run_polling()


if __name__ == '__main__':
    main()
