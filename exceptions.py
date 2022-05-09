class SendMessageError(Exception):
    """Класс для обработки ошибки при отправке сообщения в Telegram."""

    pass


class EndpointStatusError(Exception):
    """Класс для обработки ошибки cтатуса ответа сервера."""

    pass


class EndpointError(Exception):
    """Класс для обработки ошибок ответа сервера."""

    pass
