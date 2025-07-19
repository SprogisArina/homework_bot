# Homework Bot - трекер статуса домашних работ

Бот отслеживает статус проверки домашнего задания, информирует пользователя о результатах и сообщает о возможных проблемах.

## Технологии:
- python 3.9
- pyTelegramBotAPI 4.14
- REST API Практикум Домашка
- dotenv для управления переменными окружения
- Logging для системного журналирования

Автор [SprogisArina](https://github.com/SprogisArina)

## Как запустить проект:

Клонировать репозиторий:

```
git clone git@github.com:SprogisArina/homework_bot.git
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python -m venv env
```

```
source venv/Scripts/activate
```

Обновить pip и установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Создать файл .env:

```
PRACTICUM_TOKEN=токен_сервиса_практикум_домашка
TELEGRAM_TOKEN=токен_тг_бота
TELEGRAM_CHAT_ID=id_чата
```

Запустить бота:

```
python homework.py
```
