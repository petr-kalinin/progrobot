#!/usr/bin/python3
import pymongo
import re
import html

from html2tele import html2tele

client = pymongo.MongoClient()
db = client.cpp
reference = db.reference
index = db.index

def search(query):
    global reference, index
    query = re.split(r"\W+", query)
    if len(query)>7:
        return None
    if "cpp" in query:
        query.remove("cpp")
    if "c++" in query:
        query.remove("c++")
    query = " ".join(query)
    cursor = index.find({"name" : query}, sort=[("relevance", pymongo.DESCENDING)], limit=1)
    for doc in cursor:
        ref = reference.find({"_id" : doc["reference_id"]})
        for res in ref:
            subitems = [html2tele("<code>{0}</code> : {1}".format(*x)) for x in res["subitems"]]
            result ="<b>" + res["name"] + "</b> "
            if res["module"]:
                result += "<code>" + html.escape(res["module"]) + "</code>\n"
            if res["usage"]:
                result += "<pre>" + html.escape(res["usage"]) + "</pre>\n"
            result += (html2tele(res["full"]) + "\n"
                    + "\n".join(subitems) 
                    + "\n\nⓒ CppReference authors, CC-BY-SA 3.0 / GFDL, " + res["href"])
            return result
    