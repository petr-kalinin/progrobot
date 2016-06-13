import re

class Handler:
    def format_answer(self, text, **kwargs):
        text = re.sub(r"\n(\s*\n)+", "\n\n", text)
        answer = kwargs
        answer["text"] = text
        return answer
    
    def add_footer(self, answer, footer):
        if not "footer" in answer:
            answer["footer"] = []
        answer["footer"].append(footer)
    
