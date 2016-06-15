#!/usr/bin/python3
import pymongo
import re
import html
from pprint import pprint

from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

from html2tele import html2tele
from Handler import Handler
from DefaultValueHandler import DefaultValueHandler

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

INLINE_NOT_FOUND_MESSAGE = "Sorry, nothing found"

LIST_FOOTER = 'More than one reference found, type "/list {0}" to show all' 

def format_reference(res):
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

class BaseReference(object):
    def search(self, query):
        found = self.search_with_split(query, r"\s+|\:\:+|\.+")
        if not found:
            self.search_with_split(query, r"[^a-zA-Z_+-]+")
        
    def search_with_split(self, query, split_regexp):
        found = self.search_one(query.lower(), split_regexp, "name")
        if not found:
            found = self.search_one(query, split_regexp, "full_name")
        return found

    def search_one(self, query, split_regexp, key):
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
        query = filter(lambda x: x, query)
        if key == "name":
            query = sorted(query)
        query = " ".join(query)
        #print("Query: '", query, "'")
        #print("dbs: ", str(dbs))
        found = False
        for db in dbs:
            #print("db: ", str(db))
            cursor = db.index.find({key : query}, sort=[("relevance", pymongo.DESCENDING)])
            for doc in cursor:
                found = True
                need_continue = self.found_reference(db, doc)
                if not need_continue:
                    break
        return found
    

class ReferenceHandler(Handler, BaseReference):
    def handle(self, query, state):
        #print("In ReferenceHandler, query=", query)
        self.answer = None
        self.number_of_answers = 0
        self.search(query)
        if not self.answer:
            self.answer = NOT_FOUND_MESSAGE
        self.answer = {"text": self.answer}
        if self.number_of_answers > 1:
            self.add_footer(self.answer, LIST_FOOTER.format(query))
            state.set_handler("/list", DefaultValueHandler(ReferenceListHandler(), query))
        return self.format_answer(**self.answer)

    def found_reference(self, db, doc):
        self.number_of_answers += 1
        if self.number_of_answers > 1:
            return False
        ref = db.reference.find({"_id" : doc["reference_id"]})
        # will always find one result only
        for res in ref:
            self.answer = format_reference(res)
            return True

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
                     [InlineKeyboardButton(text="{0[0]} ({0[3]})".format(x), 
                                           callback_data="{0[1]} {0[3]}".format(x))]
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
                callback = re.split(r"\([^)]", res["name"])[0].split(",")[0]
                self.answers.append((res["name"], callback, relevance, db.name))
        return True
        #return relevance > self.best_relevance - EPS
        
        
class InlineReference(BaseReference):
    def add_result(self, title, text):
        text = re.sub(r"\n(\s*\n)+", "\n\n", text)
        self.answer.append({'type': 'article',
                'id': title, 
                'title': title, 
                'message_text': text,
                'parse_mode': 'HTML'})
    
    def search_inline(self, query):
        self.answer = []
        self.search(query)
        if not self.answer:
            self.add_result(INLINE_NOT_FOUND_MESSAGE, INLINE_NOT_FOUND_MESSAGE)
        return self.answer

    def found_reference(self, db, doc):
        ref = db.reference.find({"_id" : doc["reference_id"]})
        # will always find one result only
        for res in ref:
            #print("reference returns")
            #pprint(res)
            #print("ReferenceHandler result: " + result)
            self.add_result(res["name"], format_reference(res))
            return True
