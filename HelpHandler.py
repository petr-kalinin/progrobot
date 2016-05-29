from Handler import Handler

HELP_MESSAGE = """
The bot allows you to search across C++ and Python3 documentation, and across StackOverflow.

To search for documentation, just type the entity you want to search for.

For example:

std vector insert — show documentation for C++'s <code>std::vector::insert()</code> method

re — show documentation for Python3's <code>re</code> module

re match — for this specific function from <code>re</code> module

You can omit some of first tokens, for example, "vector insert" also works. You can separate tokens with any non-word characters you like, for example, "vector::insert" also works.

You can also search StackOverflow by starting your request with /so command. For example, "/so javascript print to console".

The bot is ⓒ Petr Kalinin. The bot's code is open-sources under GNU AGPL, type /license for more information.
"""

class HelpHandler(Handler):
    def handle(self, query, state):
        return self.format_answer(HELP_MESSAGE, disable_web_page_preview="True")
    
