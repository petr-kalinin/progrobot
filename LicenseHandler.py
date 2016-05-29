from Handler import Handler

LICENSE_MESSAGE = """
<b>Progrobot</b>
Copyright (C) 2016, Petr Kalinin

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as  published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the <a href="http://www.gnu.org/licenses/agpl-3.0.en.html">GNU Affero General Public License</a> for more details.
    
You can obtain the bot's source code at <a href="https://github.com/petr-kalinin/progrobot/">https://github.com/petr-kalinin/progrobot</a>.
    
<b>Answers</b>
The answers produced by this bot are covered by separate licenses; these licenses are mentioned in each particular answer.
"""

class LicenseHandler(Handler):
    def handle(self, query, state):
        return self.format_answer(LICENSE_MESSAGE, disable_web_page_preview="True")
    
