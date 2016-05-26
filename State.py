from HelpHandler import HelpHandler
from ReferenceHandler import ReferenceHandler
from StackoverflowHandler import StackoverflowHandler

class State:
    def __init__(self):
        self.handlers = {}
        self.set_handler("/help", HelpHandler())
        self.set_handler("/so", StackoverflowHandler())
        self.set_handler(None, ReferenceHandler())
        
    def __str__(self):
        res = "State: {\n"
        for command in self.handlers:
            res += str(command) + ":" + type(self.handlers[command]).__name__ +"\n"
        res += "}"
        return res
        
    def set_handler(self, command, handler):
        if handler:
            self.handlers[command] = handler
        else:
            del self.handlers[command]
            
    def handle(self, command, query):
        if command in self.handlers:
            return self.handlers[command].handle(query, self)
        else:
            raise RuntimeError("Unknown command ", command)
        
    

