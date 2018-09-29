
from __future__ import unicode_literals
import json
import logging
import requests
from alice_sdk import AliceRequest, AliceResponse
from flask import Flask, request
app = Flask(__name__)


logging.basicConfig(level=logging.DEBUG)

# Хранилище данных о сессиях.


class AliceDialog:
    def __init__(self):
        self.user_storage = {}

    def handle_dialog(self, request):  # alice_request, alice_response, session_storage
        response = AliceResponse(request)  # Создаем тело ответа

        if request.is_new_session:
            self.user_storage[''] = ''
        return response

    def make_request(self):
        pass


@app.route("/", methods=["POST"])
def post():
    alice_request = AliceRequest(request.json)
    user_id = alice_request.user_id

    if alice_request.is_new_session:
        users[user_id] = AliceDialog()

    alice_response = users[user_id].handle_dialog(alice_request)
    if alice_response.is_end:
        del users[user_id]

    return alice_response.dumps()


if __name__ == '__main__':
    users = {}
    app.run()
