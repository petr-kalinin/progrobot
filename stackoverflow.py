#!/usr/bin/python3
import html
import urllib.request
import urllib.parse
import json
import gzip
from html2tele import html2tele

def send_request(method, parameters):
    request_string = urllib.parse.urlencode(parameters)
    url = 'http://api.stackexchange.com/2.2/' + method + '?' + request_string
    print("Sending url " + url)
    response = urllib.request.urlopen(url)
    gzipfile = gzip.GzipFile(fileobj=response)
    response_bytes = gzipfile.read()
    json_string = response_bytes.decode('utf-8')
    res = json.loads(json_string)
    print(json.dumps(res, sort_keys=True, indent=4))
    return res

def get_answer(question):
    request = {
        'order': 'desc',
        'sort': 'votes',
        'site': 'stackoverflow',
        'filter': 'withbody',
        'pagesize': 1
        }
    ids = question["question_id"]
    response = send_request("/questions/{ids}/answers".format(ids=ids), request)
    return response["items"][0]

def format_user_data(post):
    return "{body} — <a href='{author_link}'>{author}</a>".format(body=html2tele(post["body"]).strip(),
                                                       author=post["owner"]["display_name"],
                                                       author_link=html.escape(post["owner"]["link"], quote=True))

def search(query):
    request = {
        'order': 'desc',
        'sort': 'relevance',
        'q': query,
        'site': 'stackoverflow',
        'filter': 'withbody',
        'pagesize': 1
        }
    response = send_request("search/advanced", request)
    question = response["items"][0]
    answer = get_answer(question)

    return (question["link"] + "\n\n"
            + "<b>" + question["title"] + "</b>\n\n" 
            + format_user_data(question) + "\n\n"
            + "<b>Answer:</b>\n\n"
            + format_user_data(answer) )
        


"""
import unittest
import unittest.mock as mock

class TestStackoverflow(unittest.TestCase):
    def test_request(self):
        with mock.patch('urllib.request.urlopen') as urlopen_mock:
            result_mock = mock.Mock()
            result_mock.readall.return_value = json.dumps({"items": [ { "body": "bodytext"}]}).encode(encoding='utf-8')
            urlopen_mock.return_value = result_mock
            result = search("test")
            self.assertEqual(result, "bodytext")

if __name__ == '__main__':
    unittest.main()
"""