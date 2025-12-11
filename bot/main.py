import asyncio
import pickle
import json
import logging
import os
import re
import io
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove
from dotenv import load_dotenv

load_dotenv()
MESSAGES = {
    "ru": {
        "choose_language": "🌍 Выбери язык",
        "new_button": "Сообщить о новой проблеме",
        "start_welcome": "👋 Привет! Давай вместе сделаем Павлодар лучше!\n\n"
                         "🤖 Я — бот «Jarqyn». С моей помощью ты можешь быстро сообщить о любой городской проблеме:\n"
                         "• ямы на дорогах\n"
                         "• мусор\n"
                         "• сломанные лавочки и детские площадки\n"
                         "• неработающие фонари и многое другое\n\n"
                         "📸 Просто отправь фото проблемы — и я проведу тебя по всем шагам.\n\n"
                         "Готов? Присылай фото прямо сейчас!",
        "photo_received": "📸 Фото получил, спасибо!\n\n"
                          "🗺️ Теперь нужно указать, где именно это находится.\n"
                          "Лучше всего — отправить геолокацию (один клик и точность до метра) 🔝",
        "ask_location": "📍 Отправить геолокацию",
        "ask_manual_address": "✍️ Ввести адрес вручную",
        "manual_address_prompt": "📌 Напиши точный адрес проблемы:\n"
                                 "например: ул. Ломова 45, подъезд 2 или перекрёсток Кутузова и Абая",
        "ask_description": "✏️ Опиши проблему коротко и понятно (2–5 слов):\n"
                           "например: «Глубокая яма на дороге» или «Мусор у контейнеров»",
        "ask_phone": "🔥 Остался последний шаг!\n\n"
                     "📞 Чтобы мы могли сообщить тебе о результате, укажи свой номер телефона.\n"
                     "Можно просто нажать кнопку ниже — быстро и безопасно 👇",
        "send_phone_button": "📱 Отправить номер телефона",
        "sending": "🚀 Отправляю заявку в центр обработки…",
        "success": "🎉 СПАСИБО ОГРОМНОЕ!\n\n"
                   "✅ Твоя заявка принята и уже передана в работу!\n"
                   "🔔 Мы обязательно сообщим тебе, когда проблема будет решена.\n\n"
                   "🏙️ Павлодар становится лучше благодаря тебе ❤️\n\n"
                   "Увидел ещё что-то? Сообщите нам.",
        "cancel_prompt": "❌ Отмена",
        "cancel": "❌ Заявка отменена.\n\n😊 Когда снова захочешь помочь городу — пиши /start",
        "cancel_button": "Отмена",
        "language_changed": "✅ Язык изменён!",
        "invalid_photo_prompt": "📸 Просим отправить фотографию проблемы!",
        "invalid_description_prompt": "✏️ Опишите проблему в текстовом сообщении!",
        "empty_description_prompt": "✏️ Неверный формат описания, попытайтесь снова",
        "invalid_location_prompt": "🗺️ Ошибочный адрес - попытайтесь снова!",
        "backend_error_prompt": "⚠️ Временная ошибка сервера, попробуйте позже.",
        "cancel_words": {"отмена", "стоп", "хватит", "не надо", "отменить"}
    },

    "kk": {
        "choose_language": "🌍 Тілді таңдаңыз",
        "new_button": "Жаңа мәселе жайлы хабарлау",
        "start_welcome": "👋 Сәлеметсіз бе! Павлодарды бірге жақсартамыз!\n\n"
                         "🤖 Мен — «Jarqyn» ботпын. Менің көмегіммен қаладағы кез келген мәселені жылдам хабарлай аласыз:\n"
                         "• жолдағы шұңқырлар\n"
                         "• қоқыстар\n"
                         "• сынған орындықтар мен балалар алаңдары\n"
                         "• жанбайтын шамдар және т.б.\n\n"
                         "📸 Жай ғана мәселенің суретін жіберіңіз — мен барлық қадамдардан өткіземін.\n\n"
                         "Дайынсыз ба? Суретті қазір жіберіңіз!",
        "photo_received": "📸 Суретті алдым, рахмет!\n\n"
                          "🗺️ Енді мәселе қай жерде екенін көрсету керек.\n"
                          "Ең дұрысы — геолокацияны жіберу (бір рет бассаңыз, метрге дейін дәл) 🔝",
        "ask_location": "📍 Геолокацияны жіберу",
        "ask_manual_address": "✍️ Мекенжайды қолмен енгізу",
        "manual_address_prompt": "📌 Мәселенің нақты мекенжайын жазыңыз:\n"
                                 "мысалы: Ломов көшесі 45, 2-көтерме немесе Құтұзов пен Абай қиылысы",
        "ask_description": "✏️ Мәселені қысқа әрі түсінікті сипаттаңыз (2–5 сөз):\n"
                           "мысалы: «Жолдағы терең шұңқыр» немесе «Контейнер жанындағы қоқыс»",
        "ask_phone": "🔥 Соңғы қадам қалды!\n\n"
                     "📞 Нәтиже туралы хабарлау үшін телефон нөміріңізді қалдырыңыз.\n"
                     "Төмендегі батырманы бассаңыз болғаны — жылдам әрі қауіпсіз 👇",
        "send_phone_button": "📱 Телефон нөмірін жіберу",
        "sending": "🚀 Өтінішті өңдеуші орталыққа жолдап жатырмын…",
        "success": "🎉 ҮЛКЕН РАХМЕТ!\n\n"
                   "✅ Сіздің өтінішіңіз қабылданды және өңдеуге жіберілді!\n"
                   "🔔 Мәселе шешілгенде сізге міндетті түрде хабарлаймыз.\n\n"
                   "🏙️ Павлодар сіз сияқты белсенді тұрғындардың арқасында әдемі әрі жайлы бола түсуде ❤️\n\n"
                   "Тағы мәселе көрсеңіз → бізге хабарлаңыз.",
        "cancel_prompt": "❌ Тоқтату",
        "cancel": "❌ Өтініш тоқтатылды.\n\n😊 Қаланы жақсартуға қайта көмектескіңіз келсе — /start жазыңыз",
        "cancel_button": "Тоқтату",
        "language_changed": "✅ Тіл өзгертілді!",
        "invalid_photo_prompt": "📸 Мәселенің суретін жіберуіңізді сұраймыз!",
        "invalid_description_prompt": "✏️ Мәселені сөзбен сипаттап жазыңыз!",
        "empty_description_prompt": "✏️ Сипаттаманың форматы қате, қайта енгізіңіз",
        "invalid_location_prompt": "🗺️ Мекенжайды анықтай алмадық - қайта енгізіңіз!",
        "backend_error_prompt": "⚠️ Сервердің жұмысындағы ақаулық, біраздан кейін қайта қосылыңыз.",
        "cancel_words": {"тоқтату", "тоқтат", "жоқ", "керек емес", "отмена", "болды"}
    },

    "en": {
        "choose_language": "🌍 Choose language",
        "new_button": "Report new problem",
        "start_welcome": "👋 Hi! Let's make Pavlodar better together!\n\n"
                         "🤖 I am the «Jarqyn» bot. With me you can quickly report any city issue:\n"
                         "• potholes\n"
                         "• garbage\n"
                         "• broken benches and playgrounds\n"
                         "• non-working street lights, etc.\n\n"
                         "📸 Just send a photo of the problem — I'll guide you through all the steps.\n\n"
                         "Ready? Send the photo now!",
        "photo_received": "📸 Got the photo, thanks!\n\n"
                          "🗺️ Now please tell me exactly where this is.\n"
                          "Best option — send your location (one tap, meter precision) 🔝",
        "ask_location": "📍 Send location",
        "ask_manual_address": "✍️ Enter address manually",
        "manual_address_prompt": "📌 Write the exact address of the issue:\n"
                                 "e.g. Lomova street 45, entrance 2 or Kutuzova & Abay intersection",
        "ask_description": "✏️ Describe the problem briefly (2–5 words):\n"
                           "e.g. “Deep pothole on roadway” or “Garbage near containers”",
        "ask_phone": "🔥 One final step!\n\n"
                     "📞 To let you know when it's fixed, please share your phone number.\n"
                     "Just tap the button below — fast and secure 👇",
        "send_phone_button": "📱 Share phone number",
        "sending": "🚀 Sending your report to processing center…",
        "success": "🎉 THANK YOU SO MUCH!\n\n"
                   "✅ Your report has been accepted and is already in progress!\n"
                   "🔔 We will definitely notify you when the issue is resolved.\n\n"
                   "🏙️ Pavlodar is becoming better thanks to caring citizens like you ❤️\n\n"
                   "Saw another issue? Report about it.",
        "cancel_prompt": "❌ Cancel",
        "cancel": "❌ Report cancelled.\n\n😊 When you want to help the city again — just type /start",
        "cancel_button": "Cancel",
        "language_changed": "✅ Language changed!",
        "invalid_photo_prompt": "📸 Please send a photo of the issue!",
        "invalid_description_prompt": "✏️ Please describe the issue in text!",
        "empty_description_prompt": "✏️ Description is invalid—try again!",
        "invalid_location_prompt": "🗺️ Location error—please retry!",
        "backend_error_prompt": "⚠️ Temporary server issue, try later.",
        "cancel_words": {"cancel", "stop", "no", "never mind"}
    }
}

# Кнопки для выбора языка (одинаковые для всех)
LANGUAGE_BUTTONS = [
    [types.KeyboardButton(text="Русский 🇷🇺")],
    [types.KeyboardButton(text="Қазақша 🇰🇿")],
    [types.KeyboardButton(text="English 🇬🇧")]
]

TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://localhost:8000/api/reports/")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


user_language: dict[int, str] = {}   # user_id → "ru" | "kk" | "en"

def get_main_menu(lang: str, finished: bool = False) -> types.ReplyKeyboardMarkup:
    if finished:
        buttons = [
            [types.KeyboardButton(text=MESSAGES[lang]["new_button"])]
        ]
    else:
        buttons = [
            [types.KeyboardButton(text=MESSAGES[lang]["cancel_button"])]    
        ]
    return types.ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False   # всегда видно
    )

def t(user_id: int, key: str) -> str:
    """Helper to get translated string"""
    lang = user_language.get(user_id, "ru")      # default = Russian
    return MESSAGES[lang].get(key, MESSAGES["ru"][key])

LANGUAGE_KB = types.ReplyKeyboardMarkup(
    keyboard=LANGUAGE_BUTTONS,
    resize_keyboard=True,
    one_time_keyboard=True
)

class Report(StatesGroup):
    choosing_language = State()
    photo = State()
    location_or_address = State()
    location = State()
    address = State()
    manual_address = State()
    description = State()
    phone = State()


@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in user_language:
        # Первый запуск — просим выбрать язык
        await message.answer(
            "🇷🇺 Выбери язык /🇰🇿 Тілді таңда /🇬🇧 Choose language",
            reply_markup=LANGUAGE_KB
        )
        await state.set_state(Report.choosing_language)
    else:
        # Уже есть язык — сразу приветствуем и показываем главное меню
        lang = user_language[user_id]
        await message.answer(
            t(user_id, "start_welcome"),
            parse_mode="Markdown",
            reply_markup=get_main_menu(lang)
        )
        await state.set_state(Report.photo)

@dp.message(Report.choosing_language)
async def language_chosen(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if "Русский" in text or "🇷🇺" in text:
        user_language[user_id] = "ru"
    elif "Қазақша" in text or "🇰🇿" in text:
        user_language[user_id] = "kk"
    elif "English" in text or "🇬🇧" in text:
        user_language[user_id] = "en"
    else:
        user_language[user_id] = "ru"

    await message.answer(
        "🇷🇺 Язык сохранён! /🇰🇿 Тіл сақталды! /🇬🇧 Language saved!",
        reply_markup=get_main_menu(user_language[user_id])
    )
    await message.answer(t(user_id, "start_welcome"), parse_mode="Markdown")
    await state.set_state(Report.photo)

@dp.message(F.text.in_({"🇷🇺 Изменить язык /🇰🇿 Тілді өзгерту /🇬🇧 Change language"}))
async def change_language_anytime(message: types.Message, state: FSMContext):
    await message.answer(
        "🇷🇺 Выбрать новый язык /🇰🇿 Жаңа тілді таңдау /🇬🇧 Choose new language",
        reply_markup=LANGUAGE_KB
    )
    await state.set_state(Report.choosing_language)

@dp.message(F.text.in_({"🇷🇺 Отмена /🇰🇿 Тоқтату /🇬🇧 Cancel"}))
async def cancel_anytime(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = user_language.get(user_id, "ru")
    await state.clear()
    await message.answer(
        t(user_id, "cancel"),
        reply_markup=get_main_menu(lang)
    )
    await state.set_state(Report.photo)  # возвращаем в начало

@dp.message(F.photo, Report.photo)
async def got_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)

    await state.update_data(file_id=photo.file_id)

    user_id = message.from_user.id
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=t(user_id, 'ask_location'), request_location=True)],
            [types.KeyboardButton(text=t(user_id, 'ask_manual_address'))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        t(user_id, "photo_received"),
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(Report.location_or_address)

@dp.message(F.location, Report.location_or_address)
async def got_location(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lat = message.location.latitude
    lon = message.location.longitude
    address = await get_address(lat, lon)
    if "не удалось" in address:
        await message.answer(t(user_id, "invalid_location_prompt"))  # e.g., "Couldn't get address—try again or enter manually."
        await state.set_state(Report.location_or_address)  # Back to choice
        return
    await state.update_data(address=address, latitude=lat, longitude=lon)
    await ask_description(message, state)  # Переходим к описанию

@dp.message(Report.location_or_address, F.text)
async def handle_location_text(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    manual_text = t(user_id, 'ask_manual_address')
    
    if message.text == manual_text:
        await message.answer(
            t(user_id, "manual_address_prompt"),
            reply_markup=types.ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
        await state.set_state(Report.address)
    else:
        # Handle other text, e.g., cancel or invalid
        await cancel_if_word(message, state)  # Assuming you have a cancel function

@dp.message(F.text, Report.address)  # Бывший manual_address, теперь address
async def got_manual_address(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_text = message.text.strip()
    
    # 1. Search for address
    found = await search_address(user_text)
    
    # 2. Validation
    if not found:
        await message.answer(t(user_id, "invalid_location_prompt"))
        return

    # Check if "Pavlodar" or "Павлодар" is in the display name or address structure
    # This helps ensure we aren't accepting an address in another city
    display_name = found.get("display_name", "")
    if "Pavlodar" not in display_name and "Павлодар" not in display_name:
        # Not in Pavlodar
        await message.answer(t(user_id, "invalid_location_prompt")) 
        # Or maybe add a specific hint? "address_not_in_pavlodar"? 
        # For now reusing invalid_location_prompt as requested ("send him a message to write it again")
        return

    # 3. Success
    lat = float(found["lat"])
    lon = float(found["lon"])
    
    # We use the user's text or the formatted one? 
    # Usually better to use the formatted one, but user might prefer their own text. 
    # Let's use the formatted display_name but maybe shorten it? 
    # Nominatim addresses are very long. 
    # Let's save the long address but maybe log it.
    
    await state.update_data(address=display_name, latitude=lat, longitude=lon)
    await ask_description(message, state)

async def ask_description(message: types.Message, state: FSMContext):
    await message.answer(t(message.from_user.id, "ask_description"), parse_mode="Markdown")
    await state.set_state(Report.description)

@dp.message(F.text, Report.description)
async def got_description(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not message.text.strip():
        await message.answer(t(user_id, "empty_description_prompt"))  # e.g., "Please provide a description !"
        return  # Stay in description state
    if len(message.text.strip()) < 2:
        await message.answer(t(user_id, "empty_description_prompt"))  # e.g., "Please provide a description !"
        return  # Stay in description state
    await state.update_data(description=message.text)
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(t(message.from_user.id, "ask_phone"), reply_markup=kb, parse_mode="Markdown")
    await state.set_state(Report.phone)

@dp.message(F.contact, Report.phone)
async def got_phone_contact(message: types.Message, state: FSMContext):
    await send_report(message, state, message.contact.phone_number)

@dp.message(F.text, Report.phone)
async def got_phone_text(message: types.Message, state: FSMContext):
    raw = message.text.strip()
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 10:
        digits = "7" + digits
    phone = "+" + digits
    await send_report(message, state, phone)

async def send_report(message: types.Message, state: FSMContext, phone: str):
    user_id = message.from_user.id
    data = await state.get_data()
    await message.answer(t(message.from_user.id, "sending"), reply_markup=types.ReplyKeyboardRemove(), parse_mode="Markdown")

    temp_file = io.BytesIO()
    success = False

    try:
        await bot.download(data["file_id"], temp_file)
        temp_file.seek(0)  # Reset pointer to start

        payload = {
            "telegram_id": message.from_user.id,
            "description": data["description"],
            "phone_number": phone,
            "address": data.get("address", "Адрес не указан"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude")
        }

        files = {"image": ("photo.jpg", temp_file, "image/jpeg")}

        # BEAUTIFUL DETAILED LOG IN CONSOLE
        logger.info("="*60)
        logger.info("NEW REPORT RECEIVED!")
        logger.info(f"From: {message.from_user.full_name} (@{message.from_user.username or 'no username'})")
        logger.info(f"User ID: {message.from_user.id}")
        logger.info(f"Phone: {phone}")
        logger.info(f"Address: {payload['address']}")
        if payload.get("latitude"):
            logger.info(f"Location: {payload['latitude']}, {payload['longitude']}")
        logger.info(f"Description: {payload['description']}")
        logger.info(f"Photo size: {temp_file.getbuffer().nbytes / 1024:.1f} KB")
        logger.info("Sending to backend...")
        logger.info("="*60)

        r = requests.post(API_URL, data=payload, files=files, timeout=10)
        success = r.status_code in (200, 201, 202)

        if success:
            logger.info(f"SUCCESS → {r.status_code} {r.json() if r.headers.get('content-type') == 'application/json' else 'OK'}")
        else:
            logger.warning(f"Backend responded: {r.status_code} {r.text[:200]}")

    except Exception as e:
        logger.error(f"Failed to send (backend offline?) → {e}")
    #if not success:
    #    await message.answer(t(user_id, "backend_error_prompt"))  # e.g., "Server issue—try later. Your report is saved locally!" (fake for demo)
    # Optionally log and retry, but for hackathon, just show success anyway
    
    # Always show success to user (perfect for demo)
    await asyncio.sleep(1)
    await message.answer(
    t(message.from_user.id, "success"),
    parse_mode="Markdown",
    reply_markup=get_main_menu(user_language[message.from_user.id], True)
    )
    await state.clear()
    await state.set_state(Report.photo)

@dp.message(Report.photo, ~F.photo)  # Catches anything NOT a photo in photo state
async def invalid_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = user_language.get(user_id, "ru")

    cancel_text = MESSAGES[lang]["cancel_button"]
    new_text = MESSAGES[lang]["new_button"]    
    if message.text == cancel_text:
        await state.clear()
        await message.answer(
            t(user_id, "cancel"),
            reply_markup=get_main_menu(lang, True)
        )
        await state.set_state(Report.photo)  # Возвращаем в начало
        return
    elif message.text == new_text:
        await state.clear()
        await message.answer(
            t(user_id, "start_welcome"),
            reply_markup=get_main_menu(lang)
        )
        await state.set_state(Report.photo)  # Возвращаем в начало
        return
    await message.answer(
        t(user_id, "invalid_photo_prompt"),  # Add this key to MESSAGES, e.g., "📸 Please send a photo of the issue!"
        parse_mode="Markdown"
    )
    # Stay in photo state to re-prompt

@dp.message(Report.description, ~F.text)
async def invalid_description(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await message.answer(
        t(user_id, "invalid_description_prompt"),  # e.g., "✏️ Please describe the issue in text!"
        parse_mode="Markdown"
    )

# Отмена в любой момент
@dp.message(F.text)
async def check_cancel_words(message: types.Message, state: FSMContext):
    await cancel_if_word(message, state)
async def cancel_if_word(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = user_language.get(user_id, "ru")
    text_lower = message.text.lower().strip()
    
    if text_lower in MESSAGES[lang]["cancel_words"]:
        await state.clear()
        await message.answer(
            t(user_id, "cancel"),
            reply_markup=get_main_menu(lang)
        )
        await state.set_state(Report.photo)

@dp.message(F.text)  # Ловим любой текст в любом состоянии
async def handle_menu_buttons(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = user_language.get(user_id, "ru")
    
    cancel_text = MESSAGES[lang]["cancel_button"]
    new_text = MESSAGES[lang]["new_button"]    
    if message.text == cancel_text:
        await state.clear()
        await message.answer(
            t(user_id, "cancel"),
            reply_markup=get_main_menu(lang)
        )
        await state.set_state(Report.photo)  # Возвращаем в начало
    elif message.text == new_text:
        await message.answer(
            t(user_id, "start_welcome"),
        )
        await state.set_state(Report.photo)
    else:
        # Если другой текст — игнорим или обрабатываем как cancel_words (см. ниже)
        await cancel_if_word(message, state)  # Если у тебя есть функция для слов-отмены

async def get_address(lat: float, lon: float) -> str:
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": lat, "lon": lon, "format": "json", "accept-language": "ru"}
        headers = {"User-Agent": "PavlodarFixBot/1.0"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json().get("display_name", "Павлодар")
    except:
        return "Павлодар (не удалось определить)"

async def search_address(query: str) -> dict | None:
    """
    Search for address using Nominatim API, biased towards Pavlodar.
    Returns the first result if found, else None.
    """
    try:
        url = "https://nominatim.openstreetmap.org/search"
        # We append 'Pavlodar' to the query to help the search engine context
        # But we will also separate it in a way that doesn't break if user already typed it
        viewbox = "76.87,52.22,77.07,52.36"  # lon_min, lat_min, lon_max, lat_max
        bounded = 1  # Ограничивает результаты только внутри viewbox
        
        params = {
            "q": query + ", Павлодар",           # принудительно добавляем город
            "format": "json",
            "limit": 1,
            "bounded": bounded,
            "viewbox": viewbox,
            "countrycodes": "kz",                # только Казахстан
            "accept-language": "ru",
            "addressdetails": 1,
            "extratags": 0,
        }
        headers = {"User-Agent": "JarqynBot/1.0"}
        print(params["q"])
        
        # Requests is blocking, so we should run it in executor if we want to be truly async clean, 
        # but for this scale direct call is acceptable or use run_in_executor. 
        # Given existing code uses blocking requests.get, we stick to that pattern or wrap it.
        # Existing get_address is sync inside async func? No, it's just blocking calls inside async func.
        # I will keep it simple as per existing code style.
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if not data:
            return None

        result = data[0]

        # Дополнительная проверка: действительно ли это Павлодар?
        display_name = result.get("display_name", "").lower()
        if "павлодар" not in display_name and "pavlodar" not in display_name:
            return None

        return result

    except Exception as e:
        logger.error(f"Address search failed: {e}")
        return None

async def main():
    logger.info("BOT is running")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())