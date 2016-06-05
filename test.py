#!/usr/bin/python3

from bs4 import BeautifulSoup

soup = BeautifulSoup("<html><body><pre>  \n\n \n<b></b></body></html>", "lxml")
print(repr(str(soup)))
