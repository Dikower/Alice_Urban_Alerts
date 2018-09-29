import requests
from typing import List, Dict


class ServerResponse:
    def __init__(self, response: requests.Response):
        self.status = bool(response)
        self.status_code = response.status_code
        self.text = response.text
        self.json = response.json()


class UserApi:
    def __init__(self, url):
        self.url = url


    def user_register(self, login: str, passwd: str, user_id: str, id_type: str) -> ServerResponse:
        pass


    def user_login(self, login: str, passwd: str) -> ServerResponse:
        pass


    def user_profile(self, user_id: str, id_type: str) -> ServerResponse:
        pass


    def problem_new(self, photo, desc: str, tags: List[str]) -> ServerResponse:
        pass


    def problem_nearest(self, address: str, prob_type: str) -> ServerResponse:
        pass


    def problem_add_comment(self, com_type: str, comment: str) -> ServerResponse:
        pass


    def problem_edit(self, prob_type: str, value: str) -> ServerResponse:
        pass


    def problem_check(self, value: str) -> ServerResponse:
        pass


    def problem_stats(self, address: str) -> ServerResponse:
        pass
