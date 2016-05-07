import html
from html.parser import HTMLParser
from html.entities import name2codepoint
import re

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
        text = "".join(self.last_text).strip()
        if not self.current_tag in CODE_TAGS:
            text = re.sub("\s+", " ", text)
        self.buf.append(text)
        self.last_text = []
        
    def push_tag(self, tag_str):
        self.process_last_text()
        self.buf.append(tag_str)
        
    def push_text(self, text):
        self.last_text.append(text)
        
    def push_newlines(self, count = 1):
        self.process_last_text()
        self.buf.append("\n" * count)

    def handle_starttag(self, tag, attrs):
        self.tag_count += 1
        if self.hide_output:
            return
        elif tag in SUPPORTED_TAGS and (self.tag_count == 1):
            self.push_tag("<"+tag+">")
            self.current_tag = tag
        elif tag == "a" and (self.tag_count == 1):
            href = find_href(attrs)
            self.push_tag("<a href='{0}'>".format(html.escape(href, quote=True)))
            self.current_tag = "a"
        elif tag in ('p', 'br', 'div', 'table'):
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
        self.tag_count -= 1

    def handle_data(self, text):
        print("data", text, self.hide_output)
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
    print("html:", html)
    parser = _HTMLToText()
    parser.feed(html)
    parser.close()
    return parser.get_text()