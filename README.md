# Телеграм-бот

## Описание

Бот-ассистент.Обращается к API сервиса Практикум.Домашка для получения статуса проверки домашних работ.

Принцип работы бота:
- с переодичностью раз в 10 минут опрашивает API сервиса Практикум.Домашка и проверяет статус отправленной на ревью домашней работы.
- при обновлении статуса анализирует ответ API и отправляет соответствующее уведомление в Telegram
- логирует свою работу и сообщает о важных проблемах сообщением в Telegram.

#### Технологии

- Python 3.7
- python-telegram-bot

#### Запуск проекта в dev-режиме

- Склонируйте репозиторий:  
``` git clone <название репозитория> ``` 
- Скопировать .env.example и назвать его .env:  
``` cp .env.example .env ```
- Заполнить переменные окружения в .env:  
``` PRACTICUM_TOKEN = токен_к_API_Практикум.Домашка ```  
``` TELEGRAM_TOKEN = токен_Вашего_Telegtam_бота ```  
``` TELEGRAM_CHAT_ID = Ваш_Telegram_ID ```
- Установите и активируйте виртуальное окружение:  
``` python -m venv venv ```  
``` source venv/Scripts/activate ``` 
- Установите зависимости из файла requirements.txt:   
``` pip install -r requirements.txt ```

#### Краткая документация к API-сервису и примеры запросов доступны по [ссылке](https://code.s3.yandex.net/backend-developer/learning-materials/delugov/%D0%9F%D1%80%D0%B0%D0%BA%D1%82%D0%B8%D0%BA%D1%83%D0%BC.%D0%94%D0%BE%D0%BC%D0%B0%D1%88%D0%BA%D0%B0%20%D0%A8%D0%BF%D0%B0%D1%80%D0%B3%D0%B0%D0%BB%D0%BA%D0%B0.pdf)

#### Автор

Гут Владимир - [https://github.com/VladimirMonolith](http://github.com/VladimirMonolith)
