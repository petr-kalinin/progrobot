import copy

import utils
from Handler import Handler

MAX_LEN = 4000
THE_ANSWER_IS_LONG = "The answer is long, type /cont to continue"

class ContinueStartHandler(Handler):
    def __init__(self, base_handler):
        self.base_handler = base_handler
        
    def __str__(self):
        return "ContinueStartHandler(" + str(self.base_handler) + ")"
        
    def handle(self, query, state):
        answer = self.base_handler.handle(query, state)
        text = answer["text"]
        if len(text) > MAX_LEN:
            result = utils.short_to_length(text, MAX_LEN - len(THE_ANSWER_IS_LONG))
            text = result[0]
            if result[1]:
                new_answer = copy.deepcopy(answer)
                new_answer["text"] = result[1]
                if "footer" in new_answer:
                    del new_answer["footer"]
                state.set_handler("/cont", ContinueHandler(new_answer))

                text = text + "\n\n..."
                self.add_footer(answer, THE_ANSWER_IS_LONG)
        else:
            state.set_handler("/cont", None)
        answer["text"] = text
        
        return self.format_answer(**answer)
    
class ContinueHandler(Handler):
    def __init__(self, answer):
        self.answer = answer
        
    def handle(self, query, state):
        return self.format_answer(**self.answer)
