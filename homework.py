import logging
import os
import sys
import time
from http import HTTPStatus

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
logger.setLevel(logging.DEBUG)
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
        response_status = response.status_code
    except requests.RequestException as error:
        raise ConnectionError(f'Сбой при запросе к эндпойнту: {error}.')
    else:
        response = response.json()
        if response_status != HTTPStatus.OK:
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
    if 'homeworks' not in response:
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
    logger.debug('Извлечение статуса домашней работы.')
    homework_keys = [
        key for key in ('status', 'homework_name') if key not in homework
    ]
    if homework_keys:
        raise KeyError(
            f'Отсутствуют ключи {",".join(homework_keys)} в ответе API.'
        )
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(
            f'Неожиданный статус домашней работы: {homework_status}.'
        )
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    logger.debug('Успешное завершение извлечения статуса.')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks = response.get('homeworks')
            if not homeworks:
                logger.debug('Обновления отсутствуют.')
                continue
            message = parse_status(homeworks[0])
            if message != previous_message:
                send_message(bot, message)
                previous_message = message
            timestamp = response.get('current_date', default=timestamp)
        # except
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.exception(message)
            if message != previous_message:
                send_message(bot, message)
                previous_message = message

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
