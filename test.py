#!/usr/bin/python3
import sys
import telepot
from telepot.delegate import per_chat_id, create_open, pave_event_space
import traceback

"""
$ python2.7 counter.py <token>
Counts number of messages a user has sent. Starts over if silent for 10 seconds.
Illustrates the basic usage of `DelegateBot` and `ChatHandler`.
"""

class MessageCounter(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        print("init")
        super(MessageCounter, self).__init__(*args, **kwargs)
        self._count = 0

    def on_chat_message(self, msg):
        try:
            print(msg)
            self._count += 1
            self.sender.sendMessage(self._count)
        except Exception as e:
            traceback.print_exc()
            


TOKEN = sys.argv[1]  # get token from command-line

bot = telepot.DelegatorBot(TOKEN, [
    pave_event_space()(
        per_chat_id(), create_open, MessageCounter, timeout=10
    ),
])
bot.message_loop(run_forever='Listening ...')