#!/usr/bin/python3
from pymongo import MongoClient
import os
import os.path
import re
import bs4
import itertools
from bs4 import BeautifulSoup

class ReferenceItem:
    def __init__(self):
        self.name = ""
        self.module = ""
        self.usage = ""
        self.short = ""
        self.full = ""
        self.fullest = ""
        self.href = ""
        self.copyright = ""
        self.subitems = []
    
    def __str__(self):
        return ("name: " + self.name + "\n"
                + "href: " + self.href + "\n"
                + "module: " + str(self.module) + "\n"
                + "usage: " + str(self.usage) + "\n"
                + "short: " + self.short + "\n\n"
                #+ "full: " + self.full + "\n\n"
                #+ "fullest: " + self.fullest + "\n\n"
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
    
def hasclass(tag, classes):
    for cl in tag.get("class", []):
        if cl in classes:
            return True
    return False

def create_ref(refs, name, module, base_href):
    if not name in refs:
        refs[name] = ReferenceItem()
    refs[name].name = name
    if module:
        refs[name].module = "import " + module
    refs[name].href = base_href +  "#" + name
    refs[name].copyright = "ⓒ Python developers, " + refs[name].href
    
    parent = ".".join(name.split(".")[:-1])
    #print(name, parent)
    if not parent in refs:
        refs[parent] = ReferenceItem()
    refs[parent].subitems.append((name, ""))
    
    
def can_be_short(text):
    #print("Testing string `" + text + "`")
    if re.match("New in version", text):
        return False
    if re.match("Source code:", text):
        return False
    return True

    
def parse_file(filename, refs):
    base_href = "https://docs.python.org/" + filename[2:]
    soup = BeautifulSoup(open(filename), 'lxml')
    module_a = soup.h1.a
    if not "headerlink" in module_a.get("class"):
        module = module_a.string
    else:
        module = None
    #print("found module", module)
    currentName = module
    if currentName:
        create_ref(refs, currentName, module, base_href)
    tag = soup.h1
    while tag:
        if isinstance(tag, bs4.element.NavigableString) or isinstance(tag, bs4.element.Comment):
            tag = tag.next_element
            continue
        #print(currentName, tag.name)
        if hasclass(tag, ["sphinxsidebar"]):
            break
        elif hasclass(tag, ["section"]):
            currentName = None
            tag = tag.next_element
        elif hasclass(tag, ['class', 'function', 'data']):
            currentName = tag.dt.get('id')
            if currentName:
                create_ref(refs, currentName, module, base_href)
                refs[currentName].usage = "".join(tag.dt.strings)[:-1].strip()
            tag = tag.dd
        elif tag.name in ("p", "pre"):
            if currentName:
                if refs[currentName].short == "":
                    text = "".join(tag.strings)
                    if can_be_short(text):
                        refs[currentName].short = "".join(str(x) for x in tag.contents)
                refs[currentName].full += str(tag)
            tag = tag.next_sibling if tag.next_sibling else tag.next_element
        else:
            tag = tag.next_element
    return refs

def insert_ref(ref, reference, index):
    result = reference.insert_one(ref.to_dict())
    #print("insert: ", ref.to_dict())
    names = [ref.name]
    for name in names:
        split_name = name.strip().split(".")
        if len(split_name) > 3:
            print(split_name," --- ", ref.name)
        for i in range(len(split_name)):
            for perm in itertools.permutations(split_name[i:]):
                subname = " ".join(perm)
                doc = {
                    "reference_id" : result.inserted_id,
                    "name" : subname,
                    "relevance" : 1-i/len(split_name),
                    "full_name" : ref.name
                    }
                #print("index: ", doc)
                index.insert_one(doc)
    
def process_file(filename, refs):
    print("\n-----------\n" + filename)
    print(".", end="", flush=True)
    parse_file(filename, refs)
    
def first_sentence(text):
    def is_balanced(text):
        for pair in ['()', '“”']:
            if text.count(pair[0]) != text.count(pair[1]):
                return False
        return True
    
    MAX_SHORT_LEN = 1000
    soup = BeautifulSoup("<html><body><p>" + text + "</html></body></p>", 'lxml').p
    res = ""
    for el in soup.children:
        if isinstance(el, bs4.element.NavigableString) and ('.' in el):
            for ch in el:
                res += ch
                if ch == '.' and is_balanced(res):
                    return res
                if el in ' ,!?()[]:;' and len(res) > MAX_SHORT_LEN:
                    return res + "..."
        else:
            res += str(el)
        if len(res) > MAX_SHORT_LEN:
            return res + "..."
        el = el.next_sibling
    return res

def finalize(refs):
    for ref_name, ref in refs.items():
        if ref.name == "":
            ref.name = ref_name
        new_subitems = []
        for item in ref.subitems:
            new_subitems.append((item[0], first_sentence(refs[item[0]].short)))
        ref.subitems = new_subitems
    
os.chdir("../raw_data/python3/docs.python.org")

client = MongoClient()
client.drop_database("python3")
db = client.python3
reference = db.reference
index = db.index
index.create_index("name")

refs = {}

for directory, subdirs, files in os.walk("."):
    for f in files:
        process_file(os.path.join(directory, f), refs)
#process_file("3/library/urllib.html", refs)
#process_file("3/library/re.html", refs)
#process_file("3/library/json.html", refs)

finalize(refs)

#print(refs)

for ref in refs.values():
    if ref.name != "":
        #print(ref)
        #print("\n")
        insert_ref(ref, reference, index)
        
#------- Testing

def assert_starts_with(text, start):
    if not text.startswith(start):
        print("Text `" + text + "` does not start with `" + start + "`")
        raise AssertionError()

def assert_ends_with(text, start):
    if not text.endswith(start):
        print("Text `" + text + "` does not end with `" + start + "`")
        raise AssertionError()

def check_urllib_parse():
    assert_starts_with(refs["urllib.parse"].short, "This module")
    found = False
    for item in refs["urllib"].subitems:
        if item[0] == "urllib.parse":
            found = True
            assert_starts_with(item[1], "This module")
            assert_ends_with(item[1], "“base URL.”")
    assert found
    
def check_unittest_mock():
    assert_starts_with(refs["unittest.mock"].short, '<a class="reference internal"')
    found = False
    for item in refs["unittest"].subitems:
        if item[0] == "unittest.mock":
            found = True
            assert_starts_with(item[1], '<a class="reference internal"')
    assert found
    
def check_urllib():
    assert_ends_with(refs["urllib"].full, "with URLs:</p>")

def check_re():
    assert len(refs["re"].subitems) > 0
    assert "re.match" in refs


check_urllib_parse()
check_unittest_mock()
check_urllib()
check_re()