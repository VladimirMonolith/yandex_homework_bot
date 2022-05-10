import logging
import os
import sys
import time
from http import HTTPStatus
from logging import Formatter, StreamHandler

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (EndpointError, EndpointStatusError, NotForSendingError,
                        SendMessageError)

load_dotenv()


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


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет информационные сообщения в Telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(f'Отправлено сообщение: {message}')
    except telegram.error.TelegramError as error:
        logger.error(f'Ошибка при отправке сообщения: {error}', exc_info=True)
        raise SendMessageError(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(current_timestamp):
    """Делает запрос к API сервиса Практикум.Домашка."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        api_response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if api_response.status_code != HTTPStatus.OK:
            logger.error(
                f'Эндпойнт {ENDPOINT} c параметрами {params} недоступен'
            )
            raise EndpointStatusError(
                f'Эндпойнт {ENDPOINT} c параметрами {params} недоступен'
            )
        return api_response.json()
    except requests.exceptions.RequestException as error:
        logger.error(
            f'Проблема при обращении к {ENDPOINT}.Ошибка {error}',
            exc_info=True
        )
        raise EndpointError(
            f'Проблема при обращении к {ENDPOINT}.Ошибка {error}'
        )


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        logger.error(
            f'Тип данных ответа API не является словарём: {response}'
        )
        raise TypeError(
            f'Тип данных ответа API не является словарём: {response}'
        )
    elif 'homeworks' not in response:
        logger.error(
            'Ключ homeworks отсутствует в ответе API.'
            f'Ключи ответа: {response.keys()}'
        )
        raise KeyError(
            'Ключ homeworks отсутствует в ответе API.'
            f'Ключи ответа: {response.keys()}'
        )
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        logger.error(
            'Тип данных значения по ключу homeworks'
            f'не является списком: {homeworks}'
        )
        raise TypeError(
            'Тип данных значения по ключу homeworks'
            f'не является списком: {homeworks}'
        )
    elif not homeworks:
        logger.debug(
            'Статус проверки домашнего задания не обновлялся'
        )
        return homeworks
    return homeworks[0]


def parse_status(homework):
    """Извлекает статус проверки домашнего задания."""
    for key in ('homework_name', 'status'):
        if key not in homework:
            logger.error(
                'Отсутствует необходимый ключ для определения статуса '
                f'проверки домашнего задания: {key}'
            )
            raise KeyError(
                'Отсутствует необходимый ключ для определения статуса '
                f'проверки домашнего задания: {key}'
            )

    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        logger.error(
            'Незадокументированный статус проверки '
            f'домашней работы: {homework_status}'
        )
        raise KeyError(
            'Незадокументированный статус проверки '
            f'домашней работы: {homework_status}'
        )
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}": {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    variables_data = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    no_value = [
        var_name for var_name, value in variables_data.items() if not value
    ]
    if no_value:
        logger.critical(
            'Отсутствует/ют обязательная/ые переменная/ые '
            f'окружения: {no_value}.'
            'Программа будет принудительно остановлена.'
        )
        return False
    logger.info('Необходимые переменные окружения доступны.')
    return True


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    error_message = ''
    homework_status_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            current_timestamp = response.get('current_date', current_timestamp)
            if homework:
                status_homework = parse_status(homework)
                if status_homework not in homework_status_message:
                    homework_status_message = status_homework
                    send_message(bot, homework_status_message)
        except NotForSendingError as error:
            message = f'Поизошла ошибка при обращении к Telegram: {error}'
            logger.error(message, exc_info=True)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message not in error_message:
                error_message = message
                logger.error(message, exc_info=True)
                send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == "__main__":
    if check_tokens():
        main()
    else:
        sys.exit(
            'Отсутствует/ют обязательная/ые переменная/ые окружения.'
            'Программа принудительно остановлена.Подробности в логах.'
        )
