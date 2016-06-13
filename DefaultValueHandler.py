import copy

import utils
from Handler import Handler

MAX_LEN = 4000
THE_ANSWER_IS_LONG = "The answer is long, type /cont to continue"

class DefaultValueHandler(Handler):
    def __init__(self, base_handler, default_query):
        self.base_handler = base_handler
        self.default_query = default_query
        
    def handle(self, query, state):
        if not query:
            query = self.default_query
        answer = self.base_handler.handle(query, state)
        return self.format_answer(**answer)
