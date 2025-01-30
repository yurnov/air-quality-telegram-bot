import os
import time
import schedule
import time
import threading
import requests
import logging
from dotenv import load_dotenv
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Load environment variables
load_dotenv()

# Environment variables
API_KEY = os.getenv('API_KEY')
TELEGRAM_BOT_API_KEY = os.getenv('TELEGRAM_BOT_API_KEY')
CITY = os.getenv('CITY')
LANGUAGE = os.getenv('LANGUAGE').lower()
CHAT_ID = os.getenv('CHAT_ID')
PULL_INTERVAL = int(os.getenv('PULL_INTERVAL', 10))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').lower()
SILENT = os.getenv('SILENT')

# Enable initial logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Validate settings
if PULL_INTERVAL < 5 or PULL_INTERVAL > 60:
    PULL_INTERVAL = 10
    logger.warning('Pull interval is invalid. Defaulting to 10 minutes')
if not API_KEY:
    logger.error('API_KEY is not set')
    exit(1)
if not TELEGRAM_BOT_API_KEY:
    logger.error('TELEGRAM_BOT_API_KEY is not set')
    exit(1)
if not CITY:
    logger.error('CITY is not set, defaulting to Lviv')
    CITY = 'lviv'
if LANGUAGE is None or LANGUAGE not in ["en", "uk", "pl"]:
    logger.warning('LANGUAGE is not set, defaulting to English')
    LANGUAGE = 'en'
if not CHAT_ID:
    logger.warning('CHAT_ID is not set, alerts will not be sent')
if LOG_LEVEL is None or LOG_LEVEL.lower() not in ["debug", "info", "warning", "error", "critical"]:
    LOG_LEVEL = "info"
    logger.info("LOG_LEVEL is not defined or invalid, using default value info")
if not SILENT or SILENT.lower() not in ["true", "false"]:
    logger.warning("SILENT is not defined in .env file, or not a boolean, using a default value false")
    SILENT = "false"
else:
    SILENT = SILENT.lower()

WAGI_FEED_API = f"https://api.waqi.info/feed/{CITY.lower()}/?token={API_KEY}"

# Global variable to store the last air quality index
location = None
location_url = None
aqi10 = None
aqi25 = None
last_aqi = None


# Function to pull data from the API
def pull_data():
    global location
    global location_url
    global aqi10
    global aqi25
    global last_aqi
    try:
        response = requests.get(WAGI_FEED_API)
        data = response.json()

        # data['data']['city']['name'] - name of sensor location
        # data['data']['city']['url'] - link to the sensor location
        # data['data']['iaqi']['pm10']['v'] - AQI for the PM10
        # data['data']['iaqi']['pm25']['v'] - AQI for the PM2.5
        # Air Quality Index scale as defined by the US-EPA 2016 standard
        # 0-50: Good, 51-100: Moderate, 101-150: Unhealthy for Sensitive Groups
        # 151-200: Unhealthy, 201-300: Very Unhealthy, 301-500: Hazardous

        aqi25 = data['data']['iaqi']['pm25']['v']
        aqi10 = data['data']['iaqi']['pm10']['v']
        location = data['data']['city']['name']
        location_url = data['data']['city']['url']

        logger.debug(f'Air quality index in {location} is {aqi10}')

        if last_aqi is not None:
            if last_aqi < 100 and aqi10 >= 100:
                send_alert('unhealthy')
            elif last_aqi < 300 and aqi10 >= 300:
                send_alert('hazardous')
            elif last_aqi >= 100 and aqi10 < 100:
                send_alert('good')
        last_aqi = aqi10
    except Exception as e:
        logger.error(f'Error pulling data: {e}')


# Function to send answer to the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user

    message = {
        "en": (
            f"Hi {user.mention_html()}, I'm a Air Quality Index bot, I will help to to know actual AQI in {CITY}. "
            f"Please use /help for more information!"
        ),
        "uk": (
            f"Привіт {user.mention_html()}, я бот індексу якості повітря, я допоможу вам дізнатися актуальний AQI в {CITY}. "
            f"Будь ласка, скористайтеся /help для отримання додаткової інформації!"
        ),
        "pl": (
            f"Cześć {user.mention_html()}, jestem botem wskaźnika jakości powietrza, pomogę Ci dowiedzieć się aktualnego AQI w {CITY}. "
            f"Skorzystaj z /help, aby uzyskać więcej informacji!"
        ),
    }

    try:

        await update.message.reply_html(message[LANGUAGE])

    except Exception as e:
        logger.error(f"Error while sending message: {e}")


# Function to send answer to the /help command
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""

    message = {
        "en": (
            f"I'm a Air Quality Index bot, I got information for {location} from {location_url}.\n\n\nPlease use command "
            f"/aqi or just send any text to get fresh data.\n\nThe air quality index (AQI) is a measure of how clean or "
            f"polluted the air is.\n\n Less than 50 considered as the Good level, 51 to 100 is Moderate, 101 to 150 is "
            f"Unhealthy for Sensitive Groups, 151 to 200 is Unhealthy, 201 to 300 is Very Unhealthy and level more than "
            f"300 considered as Hazardous.\n\n\nMore details can be found <a href='https://aqicn.org/faq/2015-03-15/air-"
            f"quality-nowcast-a-beginners-guide/'>here</a>"
        ),
        "uk": (
            f"Я бот індексу якості повітря, я отримав інформацію для {location} з {location_url}.\n\n\nБудь ласка, "
            f"скористайтеся командою /aqi або просто надішліть будь-який текст, щоб отримати свіжі дані.\n\nІндекс якості "
            f"повітря (AQI) - це показник того, наскільки чистим або забрудненим є повітря.\n\n Менше 50 вважається рівнем "
            f"Good, від 51 до 100 - Moderate, від 101 до 150 - Unhealthy for Sensitive Groups, від 151 до 200 - Unhealthy, "
            f"від 201 до 300 - Very Unhealthy, а рівень більше 300 вважається Hazardous.\n\nДодаткові відомості можна "
            f"знайти <a href='https://aqicn.org/faq/2015-03-15/air-quality-nowcast-a-beginners-guide/'>тут</a>"
        ),
        "pl": (
            f"Jestem botem wskaźnika jakości powietrza, otrzymałem informacje dla {location} z {location_url}.\n\n\nSkorzystaj "
            f"z /aqi albo po prostu wyślij dowolny tekst, aby uzyskać świeże dane.\n\nWskaźnik jakości powietrza (AQI) to miara "
            f"czystości lub zanieczyszczenia powietrza.\n\nMniej niż 50 uważa się za dobry poziom, od 51 do 100 jest umiarkowany, "
            f"od 101 do 150 jest niezdrowy dla osób wrażliwych, od 151 do 200 jest niezdrowy, od 201 do 300 jest bardzo niezdrowy, "
            f"a poziom powyżej 300 uważa się za niebezpieczny.\n\nWięcej szczegółów można znaleźć <a href='https://aqicn.org/faq/"
            f"2015-03-15/air-quality-nowcast-a-beginners-guide/'>tutaj</a>"
        ),
    }

    try:
        await update.message.reply_html(message[LANGUAGE])
    except Exception as e:
        logger.error(f"Error while sending message: {e}")


async def send_aqi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /aqi or any text is issued."""

    if None in (aqi10, aqi25):
        error_messages = {
            "en": "AQI data is not available at the moment. Please try again later.",
            "uk": "Дані AQI наразі недоступні. Спробуйте ще раз пізніше.",
            "pl": "Dane AQI nie są obecnie dostępne. Spróbuj ponownie później.",
        }
        await update.message.reply_text(error_messages[LANGUAGE])
        return

    else:

        message = {
            "en": f"Current AQI in {CITY} is {aqi10} for PM10 and {aqi25} for PM2.5.",
            "uk": f"Поточний AQI в {CITY} становить {aqi10} для PM10 та {aqi25} для PM2.5.",
            "pl": f"Aktualny AQI w {CITY} wynosi {aqi10} dla PM10 i {aqi25} dla PM2.5.",
        }

        try:
            await update.message.reply_html(message[LANGUAGE])
        except Exception as e:
            logger.error(f"Error while sending message: {e}")


# Function to send alert messages
def send_alert(level):
    if CHAT_ID:
        messages = {
            'en': {
                'unhealthy': 'Be aware, air quality reaches unhealthy levels',
                'hazardous': 'Be aware, air quality reaches hazardous levels',
                'good': 'Air quality back to a good level',
            },
            'uk': {
                'unhealthy': 'Будьте обережні, якість повітря досягає нездорового рівня',
                'hazardous': 'Будьте обережні, якість повітря досягає небезпечного рівня',
                'good': 'Якість повітря повертається до хорошого рівня',
            },
            'pl': {
                'unhealthy': 'Uważaj, jakość powietrza osiąga niezdrowy poziom',
                'hazardous': 'Uważaj, jakość powietrza osiąga niebezpieczny poziom',
                'good': 'Jakość powietrza wraca do dobrego poziomu',
            },
        }
        common_message = {
            'en': f"Air Quality Index in {CITY} is {aqi10} for PM10 and {aqi25} for PM2.5",
            'uk': f"Індекс якості повітря в {CITY} становить {aqi10} для PM10 та {aqi25} для PM2.5",
            'pl': f"Wskaźnik jakości powietrza w {CITY} wynosi {aqi10} dla PM10 i {aqi25} dla PM2.5",
        }

        text = f"{messages[LANGUAGE][level]}. {common_message[LANGUAGE]}."
        TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_API_KEY}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": text, "disable_notification": SILENT}
        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error while sending message: {e}")


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


def main() -> None:

    # Get AQI once and schedule the job to fetch every PULL_INTERVAL
    logger.info(f"Scheduling gethering AQI every {PULL_INTERVAL} minutes.")
    schedule.every(PULL_INTERVAL).minutes.do(pull_data)
    schedule.run_all()
    thread = threading.Thread(target=run_schedule)
    thread.start()

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_API_KEY).build()

    # Set logging level to defined by the user
    if LOG_LEVEL.lower() != "info":
        logger.info(f"Switching LOG_LEVEL to user-defined value {LOG_LEVEL.upper()}")
        logger.setLevel(LOG_LEVEL.upper())

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("aqi", send_aqi))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_aqi))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
