#!/usr/bin/python3
import sys
import re
import time
import threading
import random
import asyncio
import telepot
from telepot.async.delegate import per_chat_id, per_from_id, create_open
from pprint import pprint
from datetime import datetime
import traceback
import pymongo

from State import State

client = pymongo.MongoClient()
db = client.requests
requests = db.requests

def process_command(state, query, msg):
    print("In process_command")
    try:
        command = None
        print("command:", command, "query:", query)
        if "entities" in msg:
            entity = msg["entities"][0]
            if entity["type"]=="bot_command":
                l = entity["offset"]
                r = l + entity["length"]
                command = query[l:r]
                query = query[0:l] + query[r:]
        print("Current state: ", state)
        print("command:", command, "query:", query)
        answer = state.handle(command, query)
        print(answer)
        print(len(answer["text"]))
        return answer
    except Exception as e:
        traceback.print_exc()
        return "Error: " + str(type(e)) + ": " + str(e)

class ProgroBot(telepot.async.helper.ChatHandler):
    def __init__(self, seed_tuple, timeout):
        super(ProgroBot, self).__init__(seed_tuple, timeout)
        self.state = State()

    @asyncio.coroutine
    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print('Chat:', content_type, chat_type, chat_id)
        pprint(msg)
        requests.insert({"request": msg, "time": datetime.now().isoformat()})
        
        print("!", content_type)

        #if content_type != 'text':
        #    yield
        answer = process_command(self.state, msg["text"], msg)
        yield from self.sender.sendMessage(parse_mode="HTML", **answer)
            
class ProgroCallbackBot(telepot.async.helper.UserHandler):
    def __init__(self, seed_tuple, timeout):
        super(ProgroCallbackBot, self).__init__(seed_tuple, timeout)
        self.state = State()
        
    @asyncio.coroutine
    def on_callback_query(self, msg):
        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        print('Callback query:', query_id, from_id, data)            
        pprint(msg)
        requests.insert({"request": msg, "time": datetime.now().isoformat()})

        answer = process_command(self.state, msg["data"], msg)
        yield from self.sender.sendMessage(parse_mode="HTML", **answer)


TOKEN = sys.argv[1]  # get token from command-line

bot = telepot.async.DelegatorBot(TOKEN, [
    (per_chat_id(), create_open(ProgroBot, timeout=300)),
    (per_from_id(), create_open(ProgroCallbackBot, timeout=300)),
])

loop = asyncio.get_event_loop()
loop.create_task(bot.message_loop())
print('Listening ...')

loop.run_forever()