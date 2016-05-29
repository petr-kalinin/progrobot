from HelpHandler import HelpHandler

class StartHandler(HelpHandler):
    def handle(self, query, state):
        result = super().handle(query, state)
        result["text"] = "Hello!\n\n" + result["text"]
        return self.format_answer(**result)
    
