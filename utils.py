#!/usr/bin/python3
import bs4
from bs4 import BeautifulSoup
from bs4.diagnose import diagnose

import unittest

NONCOMPLETE_SENTENCE_ENDS = ',!?)]:;'

def is_balanced(text):
    for pair in ['()', '“”']:
        if text.count(pair[0]) != text.count(pair[1]):
            return False
    return True

def sentences(text, allow_noncomplete_sentence=False, min_len_for_noncomplele=0):
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
                    and el in NONCOMPLETE_SENTENCE_ENDS and 
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
    html = "<html><body><div><pre>" + text + "</pre></div></body></html>"
    soup = BeautifulSoup(html, 'lxml')
    soup = soup.pre
    res = ""
    bestScore = 0
    bestRes = ""
    for el in soup.children:
        if isinstance(el, bs4.element.NavigableString):
            #print("String '"+str(el)+"'")
            for ch in el:
                res += ch
                if is_balanced(res) and len(res) < length:
                    currentScore = None
                    if len(res)>=2 and res[-2:] == "\n\n":
                        currentScore = 1
                    elif res[-1] == "\n":
                        currentScore = 0.5
                    elif res[-1] == ".":
                        currentScore = 0.3
                    elif res[-1] in ',!?)]:;':
                        currentScore = 0.1
                    if currentScore:
                        currentScore *= len(res)
                        #print("Split attempt: ", res[-20:], currentScore, len(res), '`'+res[-2:]+'`')
                        if currentScore > bestScore:
                            bestScore = currentScore
                            bestRes = res
        else:
            #print("El: '"+str(el)+"'")
            res += str(el)
        if is_balanced(res) and len(res) < length:
            currentScore = len(res) * 0.05
            #print("Split attempt: ", res[-20:], currentScore, len(res))
            if currentScore > bestScore:
                bestScore = currentScore
                bestRes = res
        #print("res:",repr(res))
        el = el.next_sibling
    return (bestRes, res[len(bestRes):])

#----------

class TestShortToLength(unittest.TestCase):

    def test_newlines(self):
        html = "<b>a</b>\n\n<b>q</b>\n\nqwe"
        expected = ("<b>a</b>\n\n<b>q</b>\n\n", "qwe")
        self.assertEqual(short_to_length(html, len(html)-2), expected)

if __name__ == '__main__':
    unittest.main()
