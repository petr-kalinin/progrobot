#!/usr/bin/python3
import pymongo
import re
import html
from pprint import pprint

from html2tele import html2tele
from Handler import Handler

client = pymongo.MongoClient()
db_cpp = client.cpp
db_python3 = client.python3

class ReferenceHandler(Handler):
    def handle(self, query, state):
        answer = search(query)
        if not answer:
            answer = ("No reference found for your request. " +
                        "Make sure you spelled all tokens in your request propery. " +
                        "If you were asking about a specific method or function of some " +
                        "module or class, you can make your request more generic by directly asking " +
                        "about that module or class.\n\n" +
                        "If you were intending to search StackOverflow for a question, " +
                        "then prefix your request with /so command: \n" +
                        "/so " + query)
        return self.format_answer(answer)
            

def search(query):
    ans = search_one(query)
    if not ans:
        ans = search_one(query.lower())
    return ans

def search_one(query):
    query = re.split(r"[^a-zA-Z_+-]+", query)
    #print("Query: ", query)
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
    query = " ".join(filter(lambda x: x, query))
    #print("Query: ", query)
    for db in dbs:
        cursor = db.index.find({"name" : query}, sort=[("relevance", pymongo.DESCENDING)], limit=1)
        for doc in cursor:
            ref = db.reference.find({"_id" : doc["reference_id"]})
            for res in ref:
                #print("reference returns")
                #pprint(res)
                subitems = [(html.escape(x[0]), x[1]) for x in res["subitems"]]
                subitems = [html2tele("<code>{0}</code> : {1}".format(*x)) for x in subitems]
                result = ""
                if res["module"]:
                    result += "<code>" + html.escape(res["module"]) + "</code>\n"
                result = result + "<b>" + html.escape(res["name"]) + "</b>\n\n"
                if res["usage"]:
                    result += "<pre>" + html.escape(res["usage"]) + "</pre>\n\n"
                result += (html2tele(res.get("full", "")) + "\n\n"
                        + "\n".join(subitems) 
                        + "\n\n" + res["copyright"])
                return result
    