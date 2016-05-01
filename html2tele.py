# adapted from http://stackoverflow.com/questions/328356/extracting-text-from-html-file-using-python
import html
from html.parser import HTMLParser
from html.entities import name2codepoint
import re

SUPPORTED_TAGS = ('b', 'strong', 'i', 'em', 'code', 'pre')

def find_href(attrs):
    for attr in attrs:
        if attr[0] == "href":
            return attr[1]
    return ""
        

class _HTMLToText(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self._buf = []
        self.hide_output = False
        self._tag_count = 0

    def handle_starttag(self, tag, attrs):
        self._tag_count += 1
        if self.hide_output:
            return
        elif tag in SUPPORTED_TAGS and (self._tag_count == 1):
            self._buf.append("<"+tag+">")
        elif tag == "a" and (self._tag_count == 1):
            href = find_href(attrs)
            self._buf.append("<a href='{0}'>".format(html.escape(href, quote=True)))
        elif tag in ('p', 'br'):
            self._buf.append('\n')
        elif tag in ('script', 'style'):
            self.hide_output = True

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self._buf.append('\n')

    def handle_endtag(self, tag):
        if tag == 'p':
            self._buf.append('\n')
        if (tag in SUPPORTED_TAGS or tag == "a") and (self._tag_count == 1):
            self._buf.append("</" + tag + ">")
        elif tag in ('script', 'style'):
            self.hide_output = False
        self._tag_count -= 1

    def handle_data(self, text):
        if text and not self.hide_output:
            self._buf.append(html.escape(re.sub(r'\s+', ' ', text)))

    def handle_entityref(self, name):
        if name in name2codepoint and not self.hide_output:
            #c = chr(name2codepoint[name])
            self._buf.append("&" + name + ";")

    def handle_charref(self, name):
        if not self.hide_output:
            #n = int(name[1:], 16) if name.startswith('x') else int(name)
            #self._buf.append(chr(n))
            self._buf.append("&" + name + ";")

    def get_text(self):
        return re.sub(r' +', ' ', ''.join(self._buf))

def html2tele(html):
    parser = _HTMLToText()
    parser.feed(html)
    parser.close()
    return parser.get_text()