#!/usr/bin/python3
import pymongo
import re
import html
from pprint import pprint

from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

from html2tele import html2tele
from Handler import Handler

client = pymongo.MongoClient()
db_cpp = client.cpp
db_python3 = client.python3

NOT_FOUND_MESSAGE = ("No reference found for your request. "
                    "Make sure you spelled all tokens in your request propery. "
                    "If you were asking about a specific method or function of some " +
                    "module or class, you can make your request more generic by directly asking " +
                    "about that module or class.\n\n" #+
                    #"If you were intending to search StackOverflow for a question, " +
                    #"then prefix your request with /so command: \n" +
                    #"/so " + query
                    )

LIST_FOOTER = 'More than one reference found, type "/list {0}" to show all' 

class BaseReference(object):
    def search(self, query):
        found = self.search_with_split(query, r"\s+|\:\:+|\.+")
        if not found:
            self.search_with_split(query, r"[^a-zA-Z_+-]+")
        
    def search_with_split(self, query, split_regexp):
        found = self.search_one(query.lower(), split_regexp)
        return found

    def search_one(self, query, split_regexp):
        query = re.split(split_regexp, query)
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
        elif "python3" in query:
            dbs = [db_python3]
            query.remove("python3")
        else:
            dbs = [db_cpp, db_python3]
        #print("Query: '", query, "'")
        query = " ".join(sorted(filter(lambda x: x, query)))
        #print("Query: '", query, "'")
        #print("dbs: ", str(dbs))
        found = False
        for db in dbs:
            #print("db: ", str(db))
            cursor = db.index.find({"name" : query}, sort=[("relevance", pymongo.DESCENDING)])
            for doc in cursor:
                found = True
                need_continue = self.found_reference(db, doc)
                if not need_continue:
                    break
        return found
    

class ReferenceHandler(Handler, BaseReference):
    def handle(self, query, state):
        self.answer = None
        self.number_of_answers = 0
        self.search(query)
        if not self.answer:
            self.answer = NOT_FOUND_MESSAGE
        self.answer = {"text": self.answer}
        if self.number_of_answers > 1:
            self.add_footer(self.answer, LIST_FOOTER.format(query))
        return self.format_answer(**self.answer)

    def found_reference(self, db, doc):
        self.number_of_answers += 1
        if self.number_of_answers > 1:
            return False
        ref = db.reference.find({"_id" : doc["reference_id"]})
        # will always find one result only
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
            #print("ReferenceHandler result: " + result)
            self.answer = result
            return False

class ReferenceListHandler(Handler, BaseReference):
    def handle(self, query, state):
        self.answers = []
        self.best_relevance = 0
        
        self.search(query)
        
        if not self.answers:
            self.answer = NOT_FOUND_MESSAGE
            additional_parameters = {}
        else:
            if len(self.answers) > 1:
                self.answer = "Select the reference from the list below:"
            else:
                self.answer = "Only one reference found for your request:"
            markup = InlineKeyboardMarkup(inline_keyboard=[
                     [InlineKeyboardButton(text="{0[0]} ({0[2]})".format(x), 
                                           callback_data="{0[0]} {0[2]}".format(x))]
                     for x in self.answers
                 ])
            additional_parameters = {"reply_markup": markup}
                                    
        return self.format_answer(self.answer, **additional_parameters)

    def found_reference(self, db, doc):
        EPS = 1e-4
        relevance = doc["relevance"]
        if relevance > self.best_relevance + EPS:
            self.best_relevance = relevance
            #self.answers = []
        if True: #relevance > self.best_relevance - EPS:
            ref = db.reference.find({"_id" : doc["reference_id"]})
            #print("Found reference_id:", str(doc["reference_id"]))
            for res in ref:
                #print("name: ",res["name"])
                self.answers.append((res["name"], relevance, db.name))
        return True
        #return relevance > self.best_relevance - EPS
        