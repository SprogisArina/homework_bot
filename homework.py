import logging
import os
import sys
import time

import requests
from dotenv import load_dotenv
from telebot import TeleBot


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    for token in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID):
        if token is None:
            logging.critical(
                'Отсутствует обязательная переменная окружения'
            )
            sys.exit(1)


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message
    )
    logging.debug('Удачная отправка сообщения.')


def get_api_answer(timestamp):
    """Делает запрос, возавращает ответ API."""
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
        if response.status_code != 200:
            raise Exception('Статус ответа отличен от 200.')
        response = response.json()
    except requests.RequestException:
        raise Exception('Сбой при запросе к эндпойнту.')
    else:
        return response


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if isinstance(response, dict):
        homeworks = response.get('homeworks')
        current_date = response.get('current_date')
        if homeworks is None or current_date is None:
            raise KeyError('Отсутствуют ожидаемые ключи в ответе API.')
        elif not isinstance(homeworks, list):
            raise TypeError(
                'Данные под ключом "homeworks" приходят не в виде списка.'
            )
    else:
        raise TypeError('Структура данных ответа не соответствует ожиданиям.')
    return response


def parse_status(homework):
    """Извлекает статус домашней работы."""
    homework_status = homework.get('status')
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    if verdict is None:
        raise Exception('Неожиданный статус домашней работы.')
    else:
        homework_name = homework.get('homework_name')
        if homework_name is None:
            raise KeyError('Отсутствует ключ "homework_name" ')
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks = response.get('homeworks')
            if len(homeworks) != 0:
                for homework in homeworks:
                    homework_status = parse_status(homework)
                    send_message(bot, homework_status)
            else:
                logging.debug('Отсутствие в ответе новых статусов.')
            timestamp = response.get('current_date')

        except Exception as error:
            logging.error(error)
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
