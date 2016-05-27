import re

class Handler:
    def format_answer(self, text, **kwargs):
        text = re.sub(r"\n(\s*\n)+", "\n\n", text)
        answer = kwargs
        answer["text"] = text
        return answer
    
