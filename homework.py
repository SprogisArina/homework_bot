import http
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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)


class ResponseStatusException(Exception):
    """Исключение для случая, когда сатус ответа отличен от 200."""

    pass


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens = ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID')
    missing_tokens = [
        token for token in tokens if globals()[token] in (None, '')
    ]
    if missing_tokens:
        logger.critical(
            'Отсутствуют обязательные переменные окружения: '
            f'{", ".join(missing_tokens)}'
        )
        raise ValueError('Доступны не все переменные окружения.')


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    logger.debug('Начало отправки сообщения.')
    bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message
    )
    logger.debug('Удачная отправка сообщения.')


def get_api_answer(timestamp):
    """Делает запрос, возавращает ответ API."""
    logger.debug(
        f'Запрос на эндпойнт {ENDPOINT}, метка времени {timestamp}.'
    )
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
    except requests.RequestException as error:
        raise ConnectionError(f'Сбой при запросе к эндпойнту: {error}.')
    else:
        response = response.json()
        response_status = http.HTTPStatus
        if response_status != 200:
            raise ResponseStatusException(
                f'Статус ответа: {response_status}. Ожидается 200.'
            )
        logger.debug('Успешное получение ответа.')
        return response


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    logger.debug('Начало проверки ответа API.')
    if not isinstance(response, dict):
        raise TypeError(
            f'Тип данных ответа {type(response)}. Ожидается dict.'
        )
    if not ('homeworks' in response):
        raise KeyError(
            'Отсутствует ключ "homeworks" в ответе API.'
        )
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(
            f'Данные под ключом "homeworks" приходят в виде {type(homeworks)}.'
            'Ожидается list.'
        )
    logger.debug('Успешное завершение проверки ответа.')


def parse_status(homework):
    """Извлекает статус домашней работы."""
    if not 'status' in homework:
        raise 
    homework_status = homework.get('status')
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    if verdict is None:
        raise ValueError('Неожиданный статус домашней работы.')
    else:
        homework_name = homework.get('homework_name')
        if homework_name is None:
            raise KeyError('Отсутствует название домашней работы.')
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
                logger.debug('Отсутствие в ответе новых статусов.')
            timestamp = response.get('current_date')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
