import logging
import os
import sys
import time
from http import HTTPStatus
from logging import Formatter, StreamHandler

import requests
import telegram
from dotenv import load_dotenv

from exceptions import BotExceptionError

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    filename='global.log',
    format='%(asctime)s, %(levelname)s, %(name)s, '
           '%(funcName)s, %(levelno)s, %(message)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = Formatter(
    '%(asctime)s, %(levelname)s, %(name)s, '
    '%(funcName)s, %(levelno)s, %(message)s'
)
handler.setFormatter(formatter)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет информационные сообщения в Telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info(f'Отправлено сообщение: {message}')
    except telegram.error.BadRequest as error:
        logging.error(error)
        raise BotExceptionError(error)


def get_api_answer(current_timestamp):
    """Делает запрос к API сервиса Практикум.Домашка."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        api_response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as error:
        logging.error(f'Проблема с доступом к эндпойнту.Ошибка {error}')
        raise BotExceptionError(error)
    if api_response.status_code != HTTPStatus.OK:
        logging.error('Эндпойнт недоступен')
        raise BotExceptionError(
            'Сервер проверки домашнего задания недоступен'
        )
    return api_response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        logging.error('Тип данных ответа API не является словарём')
        raise TypeError('Тип данных ответа API не является словарём')
    elif 'homeworks' not in response:
        logging.error('Ключ homeworks отсутствует в ответе API')
        raise KeyError('Ключ homeworks отсутствует в ответе API')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        logging.error(
            'Тип данных значения по ключу homeworks не является списком'
        )
        raise TypeError(
            'Тип данных значения по ключу homeworks не является списком'
        )
    elif not homeworks:
        logging.debug('Статус проверки домашнего задания не обновлялся')
        return homeworks
    return homeworks[0]


def parse_status(homework):
    """Извлекает статус проверки домашнего задания."""
    for key in ('homework_name', 'status'):
        if key not in homework:
            logging.error(
                'Отсутствует необходимый ключ для определения статуса '
                f'проверки домашнего задания - {key}'
            )
            raise KeyError(
                'Отсутствует необходимый ключ для определения статуса '
                f'проверки домашнего задания - {key}'
            )

    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        logging.error(
            'Незадокументированный статус проверки домашней работы'
        )
        raise KeyError(
            'Незадокументированный статус проверки домашней работы'
        )
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}".{verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    critical_tokens_data = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    if not all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)):
        for token, value in critical_tokens_data.items():
            if not value:
                logging.critical(
                    f'Отсутствует обязательная переменная окружения: {token}.'
                    'Программа принудительно остановлена.'
                )
                return False
    logging.info('Необходимые переменные окружения доступны.')
    return True


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            current_timestamp = response.get('current_date', current_timestamp)
            if homework:
                send_message(bot, parse_status(homework))
            time.sleep(RETRY_TIME)
        except Exception as error:
            error_message = ''
            message = f'Сбой в работе программы:! {error}'
            if message not in error_message:
                error_message = message
                logging.critical(message)
                send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == "__main__":
    if check_tokens():
        main()
    else:
        SystemExit()
