class Handler:
    def format_answer(self, text, **kwargs):
        answer = kwargs
        answer["text"] = text
        return answer
    
