#!/usr/bin/python3
from pymongo import MongoClient
import os
import os.path
import re
import bs4
import itertools
from bs4 import BeautifulSoup

import utils

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
    if parent != "" and parent[0] == "@":
        parent = parent[1:]
    if not parent in refs:
        refs[parent] = ReferenceItem()
    subitem = (name, "")
    if not subitem in refs[parent].subitems:
        refs[parent].subitems.append(subitem)
    
    
def can_be_short(text):
    #print("Testing string `" + text + "`")
    if re.match("New in version", text):
        return False
    if re.match("Source code:", text):
        return False
    return True


def next_tag(tag):
    while not tag.next_sibling and tag.parent:
        tag = tag.parent
    if tag.next_sibling:
        return tag.next_sibling
    else:
        return None

    
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
    tag = soup.h1.next_sibling
    while tag is not None:
        #print("Tag: `", tag, "`")
        if isinstance(tag, bs4.element.Comment):
            tag = tag.next_element
            continue
        if isinstance(tag, bs4.element.NavigableString):
            text = tag.strip()
            if text != "" and currentName:
                if refs[currentName].short == "":
                    if can_be_short(text):
                        refs[currentName].short = text
                refs[currentName].full += text
            tag = tag.next_element
            continue
        #if currentName:
        #    print(currentName, tag.name, "`"+refs[currentName].full+"`", "\n\n")
        if hasclass(tag, ["sphinxsidebar"]):
            break
        elif hasclass(tag, ["section", "seealso"]):
            currentName = None
            tag = tag.next_element
        elif hasclass(tag, ['class', 'classmethod', 'method', 'function', 'data', 'exception', 'attribute', 'staticmethod', 'cmdoption']):
            currentName = tag.dt.get('id')
            
            usage = "".join(tag.dt.strings).strip()
            if currentName and usage[0] == "@":
                currentName = "@" + currentName
            if currentName:
                create_ref(refs, currentName, module, base_href)
                refs[currentName].usage = usage[:-1].strip()
            tag = tag.dd.next_element
        elif tag.name in ('p', 'pre', 'code', 'li', 'dt', 'dd', 'tr', 'td', 'th'):
            if (tag.name == 'p' 
                    and len(tag.contents) == 1 
                    and isinstance(tag.contents[0], bs4.element.Tag)
                    and tag.contents[0].name=="strong"):
                currentName = None
            if currentName:
                if refs[currentName].short == "":
                    text = "".join(tag.strings)
                    if can_be_short(text):
                        refs[currentName].short = "".join(str(x) for x in tag.contents)
                refs[currentName].full += str(tag)
            tag = next_tag(tag)
            if not tag:
                break
        else:
            tag = tag.next_element
    return refs

def insert_ref(ref, reference, index):
    result = reference.insert_one(ref.to_dict())
    #print("insert: ", ref.to_dict())
    names = [ref.name]
    for name in names:
        split_name = name.strip('@ ').split(".")
        if len(split_name) > 3:
            print(split_name," --- ", ref.name)
        for i in range(len(split_name)):
            perm = [x.lower() for x in split_name[i:]]
            subname = " ".join(sorted(perm))
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
    
def finalize(refs):
    for ref_name, ref in refs.items():
        if ref.name == "":
            ref.name = ref_name
        new_subitems = []
        for item in ref.subitems:
            new_subitems.append((item[0], utils.first_sentence(refs[item[0]].short)))
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
#process_file("3/library/itertools.html", refs)
#process_file("3/library/re.html", refs)
#process_file("3/library/json.html", refs)
#process_file("3/library/pprint.html", refs)
#process_file("3/library/unittest.html", refs)
#process_file("3/library/ctypes.html", refs)

finalize(refs)

#print(refs['datetime.datetime'].subitems)

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
    
def find_subitem(ref, subitem):
    found = None
    for item in ref.subitems:
        if item[0] == subitem:
            assert not found
            found = item
    return found

def check_urllib_parse():
    assert_starts_with(refs["urllib.parse"].short, "This module")
    item = find_subitem(refs["urllib"], "urllib.parse")
    assert_starts_with(item[1], "This module")
    assert_ends_with(item[1], "“base URL.”")
    
def check_unittest_mock():
    assert_starts_with(refs["unittest.mock"].short, '<a class="reference internal"')
    item = find_subitem(refs["unittest"], "unittest.mock")
    assert_starts_with(item[1], '<a class="reference internal"')
    
def check_urllib():
    assert_ends_with(refs["urllib"].full, "files</li>")

def check_re():
    assert len(refs["re"].subitems) > 0
    assert "re.match" in refs
    assert refs["re"].subitems[0][0] == "re.compile"
    assert_ends_with(refs["re"].subitems[0][1], "described below.")
    assert len(refs["re"].subitems[0][1].strip()) > 0

def check_unittest():
    assert_ends_with(refs["unittest"].full, "executing the tests.</dd>")

def check_unittest_skip():
    assert "@unittest.skip" in refs
    assert find_subitem(refs["unittest"], "@unittest.skip")
    
def check_utcnow():
    assert "datetime.datetime.utcnow" in refs
    assert find_subitem(refs["datetime.datetime"], "datetime.datetime.utcnow")
    
def check_pprint():
    assert "pprint.pprint" in refs
    assert_ends_with(refs["pprint.pprint"].full, "</pre>")
    
def check_itertools():
    assert_ends_with(refs['itertools'].full, 'vector2))</span></code>.</p>')

def check_ctypes():
    assert "ctypes.Array._length_" in refs
    assert find_subitem(refs["ctypes.Array"], "ctypes.Array._length_")
    
def check_paragraph_signs():
    found = False
    for ref in refs:
        if "¶" in refs[ref].full:
            print("¶ found in ", ref)
            found = True
    assert not found
    
check_paragraph_signs()
check_ctypes()
check_itertools()
check_re()
check_pprint()
check_utcnow()
check_urllib_parse()
check_unittest_mock()
check_urllib()
check_unittest()
check_unittest_skip()
