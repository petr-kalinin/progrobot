import bs4
from bs4 import BeautifulSoup

def sentences(text, allow_noncomplete_sentence=False, min_len_for_noncomplele=0):
    def is_balanced(text):
        for pair in ['()', '“”']:
            if text.count(pair[0]) != text.count(pair[1]):
                return False
        return True
    
    html = "<html><body><div>" + text + "</div></body></html>"
    #print("input:", html)
    soup = BeautifulSoup(html, 'lxml').div
    res = ""
    for el in soup.children:
        if isinstance(el, bs4.element.NavigableString) and ('.' in el):
            for ch in el:
                res += ch
                if ch == '.' and is_balanced(res):
                    #print("res1:" , res)
                    yield res
                    res = ""
                if (allow_noncomplete_sentence 
                    and el in ' ,!?()[]:;' and 
                    len(res) > min_len_for_noncomplele):
                    #print("res2:" , res)
                    yield res
                    res = ""
        else:
            res += str(el)
        if allow_noncomplete_sentence and len(res) > min_len_for_noncomplele:
            #print("res4:" , res)
            yield res
            res = ""
        el = el.next_sibling
    yield res
    
    
def first_sentence(text):
    MAX_SHORT_LEN = 1000
    return next(sentences(text, True, MAX_SHORT_LEN))

def short_to_length(text, length):
    if len(text) < length:
        return text
    result = ""
    sent = list(sentences(text))
    for i in range(len(sent)):
        if len("".join(sent[:i])) > length:
            return ("".join(sent[:i-1]), "".join(sent[i-1:]))
    return ("".join(sent), None)