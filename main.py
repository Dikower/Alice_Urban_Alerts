import pickle
import logging
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
        self.api = UserApi('http://urbanalerts.ml', 'alice')
        self.request = None
        self.response = None
        self.tags = ["Urban", "Social", "Eco"]
        self.conversations = {
            "new_problem": {
                0: self.get_title,
                1: self.get_description,
                2: self.get_address,
                3: self.get_tag
            },
            "nearest": {
                0: self.get_address,
                1: self.get_type,
            },
            "new_": {
            }

        }

    # Анализ сообщений для соотнесения с ключевыми словами
    def parse_message(self, message: str):
        meanings = {"профиль": "profile", "новое": "new_problem", "близжайшие": "nearest", "статистика": "stats"}
        meaning = meanings[message.split()[0]]  # TODO обработку сообщений
        return meaning

    # Выполнение на основании ключевых слов
    def execute(self, meaning: str):
        message = ""
        # if meaning == "profile":
            # response = self.api.user_profile(self.request.user_id, "alice")
            # pass
            # if response.status:
            #     self.response.set_text(f"{response.text}")
        if meaning == "new_problem":
            message = "Дайте название проблеме"
            self.user_storage["conversation"] = "new_problem"

        elif meaning == "nearest":
            message = "Назовите адрес"
            self.user_storage["conversation"] = "nearest"

        # elif meaning == "stats":
        #     pass
        # elif meaning == "comments/add":
        #     pass
        # elif meaning == "problems/solved":
        #     pass
        # elif meaning == "problems/all":
        #     pass
        # elif meaning == "problems/active":
        #     pass
        self.response.set_text('Если хотите прервать действие скажите/введите "Отмена". ' + message)

    # Сброс диалоговых переменных
    def reset_conversation(self):
        self.user_storage["conversation"] = None
        self.user_storage["state"] = 0
        self.user_storage["content"] = []

    # Функции для ConvHandler new
    # ==================================================================================================================
    def get_title(self):
        self.user_storage["state"] += 1
        self.user_storage["content"].append(self.request.command)
        self.response.set_text("Дайте описание проблемы")

    def get_description(self):
        self.user_storage["state"] += 1
        self.user_storage["content"].append(self.request.command)
        self.response.set_text("Назовите адрес места с этой проблемой.")

    def get_address(self):
        self.user_storage["state"] += 1
        self.user_storage["content"].append(self.request.command)
        self.response.set_text(f"Выберите один тег, подходящий для вашей проблемы, нажав на кнопку.")
        buttons = []
        for button in self.tags:
            buttons.append({"title": button,
                            "payload": {"pressed": True, "button": button},
                            "hide": True})
        self.response.set_buttons(buttons)

    def get_tag(self):
        tag = self.request.command.capitalize()
        if tag in self.tags:
            title, description, address = self.user_storage["content"]  # tag уже присутствует как локальная переменная
            response = self.api.problem_new(title, description, tag, address)
            logger.info(response)
            self.response.set_text(response.text)
            self.reset_conversation()
        else:
            self.response.set_text(f"Выберите один тег из доступных {', '.join(self.tags)}")

    # Функции для ConvHandler nearest
    # ==================================================================================================================
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
            self.response.set_text('Этот навык позволит вам оперативно опубликовывать '
                                   'экологические проблемы города, а также получать информацию по ним. '
                                   'Чтобы опубликовать проблему, скажите или введите "Новое".')
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
with open('users.pickle', 'wb') as file:
    pickle.dump(users, file)


@app.route("/", methods=["POST"])
def post():
    with open('users.pickle', 'rb') as file:
        users = pickle.load(file)

    alice_request = AliceRequest(request.json)
    user_id = alice_request.user_id

    if alice_request.is_new_session:
        users[user_id] = AliceDialog()  # Создаем новый диалог

    alice_response = users[user_id].handle_dialog(alice_request)
    if users[user_id].response.is_end:
        users.pop(user_id)

    with open('users.pickle', 'wb') as file:
        pickle.dump(users, file)

    return alice_response.dumps()


if __name__ == '__main__':
    app.run()
