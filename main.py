#!/usr/bin/python3
import sys
import time
import threading
import random
import telepot
from pprint import pprint
import traceback

import stackoverflow
import reference

class YourBot(telepot.Bot):
    def __init__(self, *args, **kwargs):
        super(YourBot, self).__init__(*args, **kwargs)
        self._answerer = telepot.helper.Answerer(self)
        self._message_with_inline_keyboard = None

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print('Chat:', content_type, chat_type, chat_id)
        pprint(msg)

        if content_type != 'text':
            return
        try:
            answer = reference.search(msg["text"])
            if not answer:
                answer = stackoverflow.search(msg["text"])
            print(answer)
            self.sendMessage(chat_id, answer, parse_mode="HTML")
        except Exception as e:
            self.sendMessage(chat_id, "Error: " + str(type(e)) + ": " + str(e))
            traceback.print_exc()


TOKEN = sys.argv[1]  # get token from command-line

bot = YourBot(TOKEN)
bot.message_loop()
print('Listening ...')

# Keep the program running.
while 1:
    time.sleep(10)