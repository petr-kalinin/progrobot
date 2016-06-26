#!/usr/bin/python3
from pymongo import MongoClient
import os
import os.path
import re
import bs4
import itertools
from bs4 import BeautifulSoup

class ReferenceItem:
    name = ""
    module = ""
    usage = ""
    short = ""
    full = ""
    fullest = ""
    href = ""
    copyright = ""
    subitems = []
    
    def __str__(self):
        return ("name: " + self.name + "\n"
                + "href: " + self.href + "\n"
                + "module: " + str(self.module) + "\n"
                + "usage: " + str(self.usage) + "\n"
                + "short: " + self.short + "\n\n"
                + "full: " + self.full + "\n\n"
                + "fullest: " + self.fullest + "\n\n"
                + "subitems: " + str(self.subitems)
                + "copyright: " + self.copyright)
    
    def to_dict(self):
        return {"name" : self.name,
                "href": self.href,
                "module" : self.module,
                "usage" : self.usage,
                "short" : self.short,
                "full" : self.full,
                "fullest" : self.fullest,
                "subitems" : self.subitems,
                "copyright": self.copyright}
    
def make_name(soup):
    return "".join(soup.find(id="firstHeading").strings).strip()

def make_module(soup):
    text = soup.find(string="Defined in header ")
    if not text:
        return None
    header = text.next_sibling
    return "#include " + "".join(header.string).strip()

def make_usage(soup):
    table = soup.find(class_="t-dcl-begin")
    if not table:
        return None
    elements = table.find_all(name="tbody")
    result = ""
    for element in elements:
        codes = element.find_all(class_="cpp")
        #print(codes)
        result = result + "\n".join("".join(s for s in c.strings) for c in codes)
        version = element.find(string=re.compile(r'\s*\(\d+\)\s*'))
        if version:
            result = result + "  // " + version.string.strip()
        result = result + "\n"
    result = re.sub(r'\n+', '\n', result)
    return result.strip()

def make_desc(soup):
    p = soup.select("#mw-content-text > p:nth-of-type(1)")
    if len(p) == 0:
        return (None, None, None)
    short = "".join(str(x) for x in p[0].contents).strip()
    el = p[0]
    full = ""
    fullest = ""
    in_full = True
    while el:
        if isinstance(el, bs4.element.Tag) and (
                el.get("id") == "toc" or el.name == "h3" or 
                ("t-dsc-begin" in el.get("class", []))):
            in_full = False
        if not isinstance(el, bs4.element.Comment):
            if in_full:
                full = full + str(el)
            fullest = fullest + str(el)
        el = el.next_sibling
    
    return (short, full, fullest)

def make_subitems(soup, filename, name):
    all_dsc = soup.find_all(class_="t-dsc")
    subitems = []
    needed_dir = os.path.splitext(os.path.basename(filename))[0]
    for dsc in all_dsc:
        a = dsc.a
        if not a:
            continue
        href = a.get("href")
        if not href:
            continue
        if (not href.startswith(needed_dir + "/")) and (not name.startswith("Standard library header")):
            continue
        for tag in dsc.find_all(class_="t-mark"):
            tag.decompose()
        subitem = []
        for child in a.children:
            if isinstance(child, bs4.element.Tag):
                for cchild in child.children:
                    if isinstance(cchild, bs4.element.Tag):
                        subitem.append("".join(cchild.strings).strip())
        subitem = "\n".join(subitem)
        tr2 = dsc.select("> td:nth-of-type(2)")
        if not tr2:
            continue
        desc = "".join(tr2[0].strings).strip()
        subitems.append((subitem, desc))
    return subitems

def correct_code(soup):
    for tag in soup(class_="mw-geshi"):
        tag.name = "code"
        tag.attrs = {}

def parse_file(filename):
    soup = BeautifulSoup(open(filename), 'lxml')
    ref = ReferenceItem()
    ref.href = "http://en.cppreference.com/w/cpp/" + filename
    ref.name = make_name(soup)
    ref.module = make_module(soup)
    ref.usage = make_usage(soup)
    correct_code(soup)  # only after usage
    ref.short, ref.full, ref.fullest = make_desc(soup)
    ref.subitems = make_subitems(soup, filename, ref.name)
    ref.copyright = "ⓒ CppReference authors, CC-BY-SA 3.0 / GFDL, " + ref.href
    return ref

def process_file(filename, reference, index):
    #print("\n-----------\n" + filename)
    print(".", end="", flush=True)
    ref = parse_file(filename)
    result = reference.insert_one(ref.to_dict())
    #print("insert: ", ref.to_dict())
    corrector = 1
    name = ref.name
    match1 = re.match(r"Standard library header <(\w+)>", name)
    if match1:
        name = match1.group(1)
        corrector = 0.1
    #print("name: ", name)
    # for vector<bool>, etc
    name = re.sub(r"<(void|char|bool)>", r"::\1", name)
    #print("name: ", name)
    # for hash<Key>, etc
    name = re.sub(r"<\w+>", "", name)
    names = re.split(r"\([^)]", name)[0].split(",")
    #print("name: ", name)
    #print("names: ", names)
    for name in names:
        split_name = name.strip().split("::")
        if len(split_name) > 6:
            print(split_name," --- ", ref.name)
        for i in range(len(split_name)):
            perm = [x.lower() for x in split_name[i:]]
            subname = " ".join(sorted(perm))
            #fix for std::vector<bool> etc
            if subname == "bool" or subname == "char": 
                continue
            doc = {
                "reference_id" : result.inserted_id, 
                "name" : subname,
                "relevance" : (1-i/len(split_name)) * corrector,
                "full_name" : ref.name
                }
            #print("index: ", doc)
            index.insert_one(doc)
    
os.chdir("../raw_data/cpp/reference/en/cpp")

client = MongoClient()
client.drop_database("cpp")
db = client.cpp
reference = db.reference
index = db.index
index.create_index("name")

for directory, subdirs, files in os.walk("."):
    for f in files:
        process_file(os.path.join(directory, f), reference, index)
#process_file("container.html", reference, index)
#process_file("container/vector_bool.html", reference, index)
#process_file("container/vector.html", reference, index)
#process_file("container/vector/insert.html", reference, index)
#process_file("experimental/fs/path.html", reference, index)
#process_file("header/vector.html", reference, index)