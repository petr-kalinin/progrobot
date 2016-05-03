#!/usr/bin/python3
import pymongo
import re
import html

from html2tele import html2tele

client = pymongo.MongoClient()
db_cpp = client.cpp
db_python3 = client.python3

def search(query):
    query = re.split(r"\W+", query)
    if len(query)>7:
        return None
    dbs = []
    if "cpp" in query:
        dbs = [db_cpp]
        query.remove("cpp")
    elif "c++" in query:
        dbs = [db_cpp]
        query.remove("c++")
    elif "python" in query:
        dbs = [db_python3]
        query.remove("python")
    else:
        dbs = [db_cpp, db_python3]
    query = " ".join(query)
    for db in dbs:
        cursor = db.index.find({"name" : query}, sort=[("relevance", pymongo.DESCENDING)], limit=1)
        for doc in cursor:
            ref = db.reference.find({"_id" : doc["reference_id"]})
            for res in ref:
                subitems = [html2tele("<code>{0}</code> : {1}".format(*x)) for x in res["subitems"]]
                result ="<b>" + res["name"] + "</b> "
                if res["module"]:
                    result += "<code>" + html.escape(res["module"]) + "</code>"
                result += "\n\n"
                if res["usage"]:
                    result += "<pre>" + html.escape(res["usage"]) + "</pre>\n"
                result += (html2tele(res.get("full", "")) + "\n"
                        + "\n".join(subitems) 
                        + "\n\n" + res["copyright"])
                return result
    