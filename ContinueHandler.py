import copy

import utils
from Handler import Handler

MAX_LEN = 4096

class ContinueStartHandler(Handler):
    def __init__(self, base_handler):
        self.base_handler = base_handler
        
    def handle(self, query, state):
        answer = self.base_handler.handle(query, state)
        text = answer["text"]
        if len(text) > MAX_LEN:
            result = utils.short_to_length(text, MAX_LEN - 100)
            text = result[0]
            if result[1]:
                text = text + "\n\n" + "... (The answer is long, type /cont to continue)"
                new_answer = copy.deepcopy(answer)
                new_answer["text"] = result[1]
                state.set_handler("/cont", ContinueHandler(new_answer))
        else:
            state.set_handler("/cont", None)
        answer["text"] = text
        
        return self.format_answer(**answer)
    
class ContinueHandler(Handler):
    def __init__(self, answer):
        self.answer = answer
        
    def handle(self, query, state):
        return self.format_answer(**self.answer)
