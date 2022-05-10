class NotForSendingError(Exception):
    """Класс для ошибок, которые не предназначены для отправки в Telegram."""

    pass


class SendMessageError(NotForSendingError):
    """Класс для обработки ошибки при отправке сообщения в Telegram."""

    pass


class EndpointStatusError(Exception):
    """Класс для обработки ошибки cтатуса ответа сервера."""

    pass


class EndpointError(Exception):
    """Класс для обработки ошибок ответа сервера."""

    pass
