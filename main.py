#!/usr/bin/python3
import logging
import sys
import re
import time
import threading
import random
import telepot
from telepot.delegate import per_chat_id, per_from_id, per_inline_from_id, create_open, pave_event_space
from pprint import pprint
from datetime import datetime
import traceback
import pymongo
import pdb

from State import State
from ReferenceHandler import InlineReference

BOT_NAME="progrobot"

client = pymongo.MongoClient()
db = client.requests
requests = db.requests

def process_command(state, query, msg):
    #print("In process_command")
    try:
        command = None
        #print("command:", command, "query:", query)
        if "entities" in msg:
            entity = msg["entities"][0]
            if entity["type"]=="bot_command":
                l = entity["offset"]
                r = l + entity["length"]
                command = query[l:r]
                query = query[0:l] + query[r:]
                command = command.lower()
                bot_ref = "@" + BOT_NAME
                if command.endswith(bot_ref):
                    command = command[:-len(bot_ref)]
        print("Current state: ", state)
        #print("command:", command, "query:", query)
        answer = state.handle(command, query)
        print(answer)
        print(len(answer["text"]))
        return answer
    except Exception as e:
        traceback.print_exc()
        return {"text": "Error: " + str(type(e))}
    
def force_chat_id(msg):
    #print("In force_chat_id")
    if "chat" in msg:
        pass
    elif "message" in msg:
        msg["chat"] = {"id": msg["message"]['chat']['id']}
    elif "from" in msg:
        msg["chat"] = {"id": msg["from"]["id"]}

class ProgroBot(telepot.helper.ChatHandler):
    def __init__(self, seed_tuple, *args, **kwargs):
        try:
            #print("In constructor", seed_tuple)
            msg = seed_tuple[1]
            force_chat_id(msg)
            seed_tuple = (seed_tuple[0], msg, seed_tuple[2])
            super(ProgroBot, self).__init__(seed_tuple, *args, **kwargs)
            self.state = State()
        except Exception as e:
            traceback.print_exc()
            print("Error in constructor: " + str(e))

    def on_chat_message(self, msg):
        try:
            #print("In on_chat_message")
            content_type, chat_type, chat_id = telepot.glance(msg)
            print('Chat:', content_type, chat_type, chat_id)
            pprint(msg)
            requests.insert({"request": msg, "time": datetime.now().isoformat()})
            
            answer = process_command(self.state, msg["text"], msg)
            self.sender.sendMessage(parse_mode="HTML", **answer)
        except Exception as e:
            traceback.print_exc()
            print("Error: " + str(e))
            self.sender.sendMessage("Error: " + str(e))
            
    def on_callback_query(self, msg):
        try:
            #print("In on_callback_query")
            query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
            print('Callback query:', query_id, from_id, data)            
            pprint(msg)
            requests.insert({"request": msg, "time": datetime.now().isoformat()})

            answer = process_command(self.state, msg["data"], msg)
            self.sender.sendMessage(parse_mode="HTML", **answer)
        except Exception as e:
            traceback.print_exc()
            print("Error: " + str(e))
            self.sender.sendMessage("Error: " + str(e))
            
class InlineProgroBot(telepot.helper.UserHandler):
    def __init__(self, *args, **kwargs):
        super(InlineProgroBot, self).__init__(*args, flavors=['inline_query', 'chosen_inline_result'], **kwargs)
        self._answerer = telepot.helper.Answerer(self.bot)

    def on_inline_query(self, msg):
        query_id, from_id, query_string = telepot.glance(msg, flavor='inline_query')
        #print(self.id, ':', 'Inline Query:', query_id, from_id, query_string)

        def compute_answer():
            ir = InlineReference()
            result = ir.search_inline(query_string)
            #print("Inline result: ", result)
            return result

        self._answerer.answer(msg, compute_answer)

    def on_chosen_inline_result(self, msg):
        result_id, from_id, query_string = telepot.glance(msg, flavor='chosen_inline_result')
        #print(self.id, ':', 'Chosen Inline Result:', result_id, from_id, query_string)
        
        
def per_real_chat_id(msg):
    if "chat" in msg:
        return msg['chat']['id']
    elif "message" in msg:
        return msg["message"]['chat']['id']
    elif "from" in msg:
        return msg["from"]["id"]
    print("?!")
    return [] # forces to launch new delegator each time


# DelegatorBot works wrongly with callback
# so we convert callback to ordinary message
class DelegatorBotFixed(telepot.DelegatorBot):
    def handle(self, msg):
        if "message" in msg:
            new_msg = {'chat': msg['message']['chat'],
                        'date': msg['message']['date'],
                        'from': msg['from'],
                        'message_id': msg['message']['message_id'],
                        'text': msg['data']}
        else:
            new_msg = msg
        print("mgs=", new_msg)
        super().handle(new_msg)

TOKEN = sys.argv[1]  # get token from command-line

bot = DelegatorBotFixed(TOKEN, [
    pave_event_space()(per_inline_from_id(), create_open, InlineProgroBot, timeout=300),
    pave_event_space()(per_real_chat_id, create_open, ProgroBot, timeout=300),
])


print('Listening ...')

bot.message_loop(run_forever=True)