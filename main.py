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

import stackoverflow
import reference
import utils

client = pymongo.MongoClient()
db = client.requests
requests = db.requests

HELP_MESSAGE = """
The bot allows you to search across C++ and Python3 documentation, and across StackOverflow.

To search for documentation, just type the entity you want to search for.

For example:

std vector insert — show documentation for C++'s <code>std::vector::insert()</code> method

re — show documentation for Python3's <code>re</code> module

re match — for this specific function from <code>re</code> module

You can omit some of first tokens, for example, "vector insert" also works. You can separate tokens with any non-word characters you like, for example, "vector::insert" also works.

You can also search StackOverflow by starting your request with /so command. For example, "/so javascript print to console".

The bot is ⓒ Petr Kalinin, GNU AGPL, <a href="https://github.com/petr-kalinin/progrobot">github.com/petr-kalinin/progrobot</a>
"""

MAX_LEN = 4096

class ProgroBot(telepot.async.helper.ChatHandler):
    def __init__(self, seed_tuple, timeout):
        super(ProgroBot, self).__init__(seed_tuple, timeout)
        self._count = 0

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
            additional_parameters = {}
            if query == "/start" or query == "/help":
                answer = HELP_MESSAGE
                additional_parameters["disable_web_page_preview"] = "True"
            elif query == "/so":  # TODO: accept also /so@Progrobot
                answer = "Please follow /so command by actual request to StackOverflow"
            elif query[0:4] == "/so ":
                answer = stackoverflow.search(query)
            else:
                answer = reference.search(query)
                if not answer:
                    answer = ("No reference found for your request. " +
                              "Make sure you spelled all tokens in your request propery. " +
                              "If you were asking about a specific method or function of some " +
                              "module or class, you can make your request more generic by directly asking " +
                              "about that module or class.\n\n" +
                              "If you were intending to search StackOverflow for a question, " +
                              "then prefix your request with /so command: \n" +
                              "/so " + query)
            answer = re.sub(r'\n(\s*\n+)', '\n\n', answer)
            if len(answer) > MAX_LEN:
                answer = utils.short_to_length(answer, MAX_LEN - 100)
                answer = answer + "\n\n" + "... (The answer is long, type /cont to continue)"
            print(answer)
            print(len(answer))
            yield from self.sender.sendMessage(answer, parse_mode="HTML", **additional_parameters)
        except Exception as e:
            self.sendMessage(chat_id, "Error: " + str(type(e)) + ": " + str(e))
            traceback.print_exc()


TOKEN = sys.argv[1]  # get token from command-line

bot = telepot.async.DelegatorBot(TOKEN, [
    (per_chat_id(), create_open(ProgroBot, timeout=10)),
])

loop = asyncio.get_event_loop()
loop.create_task(bot.message_loop())
print('Listening ...')

loop.run_forever()