#!/usr/bin/python3
import sys
import re
import time
import threading
import random
import asyncio
import telepot
from telepot.async.delegate import per_chat_id, create_open
from pprint import pprint
from datetime import datetime
import traceback
import pymongo

from State import State

client = pymongo.MongoClient()
db = client.requests
requests = db.requests

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

        if content_type != 'text':
            yield
        try:
            query = msg["text"]
            command = None
            print("command:", command, "query:", query)
            if "entities" in msg:
                entity = msg["entities"][0]
                if entity["type"]=="bot_command":
                    l = entity["offset"]
                    r = l + entity["length"]
                    command = query[l:r]
                    query = query[0:l] + query[r:]
            print("Current state: ", self.state)
            print("command:", command, "query:", query)
            answer = self.state.handle(command, query)
            print(answer)
            print(len(answer["text"]))
            yield from self.sender.sendMessage(parse_mode="HTML", **answer)
        except Exception as e:
            yield from self.sender.sendMessage("Error: " + str(type(e)) + ": " + str(e))
            traceback.print_exc()


TOKEN = sys.argv[1]  # get token from command-line

bot = telepot.async.DelegatorBot(TOKEN, [
    (per_chat_id(), create_open(ProgroBot, timeout=10)),
])

loop = asyncio.get_event_loop()
loop.create_task(bot.message_loop())
print('Listening ...')

loop.run_forever()