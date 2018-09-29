from __future__ import unicode_literals
import logging
import requests
from alice_sdk import AliceRequest, AliceResponse
from api import UserApi, ServerResponse
from flask import Flask, request

app = Flask(__name__)
logging.basicConfig(format='[%(asctime)s][%(levelname)s] - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class AliceDialog:
    def __init__(self):
        self.user_storage = {}
        self.api = UserApi("our_server.com")
        self.request = None
        self.response = None
        self.tags = ["урбанистика", "общество", "экология"]
        self.conversations = {
            "new": {
                0: self.get_description,
                1: self.get_tags,
            },
            "nearest": {
                0: self.get_address,
                1: self.get_type,
            },

        }

    # Анализ сообщений для соотнесения с ключевыми словами
    def parse_message(self, message: str):
        meanings = {"профиль": "profile", "новые": "new", "близжайшие": "nearest", "статистика": "stats"}
        meaning = meanings[message.split()[0]]  # TODO обработку сообщений
        return meaning

    # Выполнение на основании ключевых слов
    def execute(self, meaning: str):
        if meaning == "profile":
            response = self.api.user_profile(self.request.user_id, "alice")
            if response.status:
                self.response.set_text(f"{response.text}")
        elif meaning == "new":
            self.response.set_text("Дайте описание проблемы")
            self.user_storage["conversation"] = "new"

        elif meaning == "nearest":
            self.user_storage["conversation"] = "nearest"
            self.response.set_text("Назовите адресс")  # TODO исправить вывод

        elif meaning == "stats":
            pass
        elif meaning == "comments/add":
            pass
        elif meaning == "problems/solved":
            pass
        elif meaning == "problems/all":
            pass
        elif meaning == "problems/active":
            pass

    # Сброс диалоговых переменных
    def reset_conversation(self):
        self.user_storage["conversation"] = None
        self.user_storage["state"] = 0
        self.user_storage["content"] = []

    # Функции для ConvHandler new
    # ==================================================================================================================
    def get_description(self):
        self.user_storage["state"] += 1
        self.user_storage["content"].append(self.request.command)
        self.response.set_text(f"Добавьте теги, доступные: {', '.join(self.tags)}.")  # TODO исправить вывод

    def get_tags(self):
        tags = self.request.command.lower().split()
        self.user_storage["state"] += 1

        correct = True
        for tag in tags:
            if tag not in self.tags:
                correct = False
                break
        if correct:
            self.user_storage["content"].append(tags)
            photo, descr, tags = self.user_storage["content"]
            response = self.api.problem_new(photo, descr, tags)
            self.response.set_text(response.text)  # TODO response.text from api
            self.reset_conversation()
        else:
            self.response.set_text(f"Выберите теги из {', '.join(self.tags)}")
    # ==================================================================================================================

    # Функции для ConvHandler nearest
    # ==================================================================================================================
    def get_address(self):
        self.user_storage["state"] += 1
        self.user_storage["content"].append(self.request.command)
        self.response.set_text("Назовите теги, которые вас интересуют.")

    def get_type(self):
        self.user_storage["state"] += 1
        tags = self.request.command.lower()
        correct = True
        for tag in tags:
            if tag not in self.tags:
                correct = False
                break
        if correct:
            self.user_storage["content"].append(self.request.command)
            self.api.problem_nearest()  # TODO
            self.response.set_text("")
            self.reset_conversation()
        else:
            self.response.set_text(f"Выберите теги из {', '.join(self.tags)}")
    # ==================================================================================================================
    
    # Основной обработчик
    def handle_dialog(self, request: AliceRequest) -> AliceResponse:  # alice_request, alice_response, session_storage
        self.request = request
        logger.info(request)
        self.response = AliceResponse(self.request)  # Создаем тело ответа

        if self.request.is_new_session:
            self.user_storage["conversation"] = None
            self.user_storage["state"] = 0
            self.user_storage["content"] = []
            self.response.set_text("Этот навык позволит вам оперативно опубликовывать"
                                   " экологические проблемы города, а также получать информацию по ним.")
            return self.response

        if self.user_storage["conversation"] is None:
            message = self.request.command.lower().strip()  # .replace()
            # Предобработка message
            meaning = self.parse_message(message)
            self.execute(meaning)
        else:
            if self.request.command.lower().strip() == "отмена":
                self.reset_conversation()
                self.response.set_text("Действие отменено")
            else:
                input_functions = self.user_storage["conversation"]
                state = self.user_storage["state"]
                self.conversations[input_functions][state]()  # Запускаем функцию из очереди

        return self.response


users = {}


@app.route("/", methods=["POST"])
def post():
    alice_request = AliceRequest(request.json)
    user_id = alice_request.user_id

    if alice_request.is_new_session:
        users[user_id] = AliceDialog()  # Создаем новый диалог

    alice_response = users[user_id].handle_dialog(alice_request)
    if alice_response.is_end:
        users.pop(user_id)

    return alice_response.dumps()


if __name__ == '__main__':
    app.run()
