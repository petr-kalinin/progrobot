#!/usr/bin/python3
import html
from html.parser import HTMLParser
from html.entities import name2codepoint
import re

import unittest

SUPPORTED_TAGS = ('b', 'strong', 'i', 'em', 'code', 'pre')
CODE_TAGS = ('code', 'pre')

def find_href(attrs):
    for attr in attrs:
        if attr[0] == "href":
            return attr[1]
    return ""
        

class _HTMLToText(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.buf = []
        self.last_text = []
        self.hide_output = False
        self.tag_count = 0
        self.current_tag = None
        
    def process_last_text(self):
        text = "".join(self.last_text)
        if not self.current_tag in CODE_TAGS:
            text = re.sub("\s+", " ", text)
        self.buf.append(text)
        self.last_text = []
        
    def push_tag(self, tag_str):
        print("push_tag", tag_str)
        if len(tag_str) >= 2 and tag_str[1] != "/":
            self.tag_count += 1
        else:
            self.tag_count -= 1
        self.process_last_text()
        self.buf.append(tag_str)
        
    def push_text(self, text):
        self.last_text.append(text)
        
    def push_newlines(self, count = 1):
        self.process_last_text()
        self.buf.append("\n" * count)

    def handle_starttag(self, tag, attrs):
        if self.hide_output:
            return
        if self.tag_count != 0:
            self.tag_count += 1
        if tag in SUPPORTED_TAGS and (self.tag_count == 0):
            self.push_tag("<"+tag+">")
            self.current_tag = tag
        elif tag == "a" and (self.tag_count == 0):
            href = find_href(attrs)
            self.push_tag("<a href='{0}'>".format(html.escape(href, quote=True)))
            self.current_tag = "a"
        elif tag in ('p', 'br', 'div', 'table','dt','dd','li'):
            self.push_newlines(2)
        elif tag in ('script', 'style'):
            self.hide_output = True

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self.push_newlines(2)

    def handle_endtag(self, tag):
        if tag in ('p', 'div', 'table'):
            self.push_newlines(2)
        elif (tag in SUPPORTED_TAGS or tag == "a") and (self.tag_count == 1):
            self.push_tag("</" + tag + ">")
            self.current_tag = None
        elif tag in ('script', 'style'):
            self.hide_output = False
        if self.tag_count != 0:
            self.tag_count -= 1

    def handle_data(self, text):
        if not self.hide_output:
            self.push_text(html.escape(text))

    def handle_entityref(self, name):
        if name in name2codepoint and not self.hide_output:
            code = name2codepoint[name]
            self.push_text("&#" + str(code) + ";")

    def handle_charref(self, name):
        if not self.hide_output:
            self.push_text("&" + name + ";")

    def get_text(self):
        self.push_tag("")
        res = ''.join(self.buf)
        return res

def html2tele(html):
    print("html2tele input: ", html)
    parser = _HTMLToText()
    parser.feed(html)
    parser.close()
    result = parser.get_text()
    result = re.sub(r'\n(\s*\n+)', '\n\n', result)
    print("html2tele result: ", result)
    return result

#----------

class TestHtml2Tele(unittest.TestCase):

    #@unittest.skip
    def test_spaces_around_tags(self):
        html = "The <a href=''>urllib.error</a> module"
        expected = "The <a href=''>urllib.error</a> module"
        self.assertEqual(html2tele(html), expected)

    #@unittest.skip
    def test_code_in_other(self):
        html = "<div><code>tmp</code></div>"
        expected = "\n\n<code>tmp</code>\n\n"
        self.assertEqual(html2tele(html), expected)

    def test_code_in_pre(self):
        html = "<pre><code>tmp</code></pre>"
        expected = "<pre>tmp</pre>"
        self.assertEqual(html2tele(html), expected)

if __name__ == '__main__':
    unittest.main()