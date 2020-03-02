"""Bitrix24 Timeman Commandline Tool

Dependencies
------------
Use virtualenv or install globally: 
pip3 install bs4 requests


Auto open and close workday
---------------------------
Use crontab for scheduling, for example:

Start workday at 8:00 from monday to friday:
0 8 * * 1-5 /usr/bin/python3 b24timeman-cli start >/dev/null 2>&1

End workday at 20:00 from monday to friday:
0 20 * * 1-5 /usr/bin/python3 b24timeman-cli close >/dev/null 2>&1

Please, use external randomization tool for random start and end time.

"""

__version__ = "1.0.0"
__author__ = "Vladimir Krasnov <v@krsnv.ru>"

import os
import sys
import requests
import hashlib
import configparser

from bs4 import BeautifulSoup


CONFIG_PATH = str(os.path.join(os.getenv("HOME"), ".b24timeman.conf"))

if not os.path.exists(CONFIG_PATH):
    print("Please, create ~/.b24timeman.conf with your configuration")
    print("""
[Bitrix]
base_url = https://your-bitrix24-instance

[User]
login = yourname@example.com
pass = your_secret_pass
user_agent = Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0

""")
    quit()

config = configparser.ConfigParser()

with open(CONFIG_PATH, 'r') as cfile:
    config.read_string(cfile.read())


BASE_URL = config.get('Bitrix', 'base_url')

AUTH_ROUTE = "/"
TIMEMAN_ROUTE = "/bitrix/tools/timeman.php"

USER_AGENT = config.get('User', 'user_agent')
USER_DEVICE = "browser"

# Bitrix user credentials
USER_LOGIN = config.get('User', 'login')
USER_PASS = config.get('User', 'pass')

HEADERS = {
    "Bx-ajax": "true",
    "User-agent": USER_AGENT,
    "TE": "Trailers"
}

AUTH_DATA = {
    "USER_LOGIN": USER_LOGIN,
    "USER_PASSWORD": USER_PASS,
    "TYPE": "AUTH",
    "AUTH_FORM": "Y"
}

FORM_DATA = {
    "device": USER_DEVICE,
    "newActionName": None # continue
}


def is_alive():
    r = requests.get(BASE_URL + AUTH_ROUTE)
    if r.status_code == 200:
        return True
    else:
        return False


def auth(session):
    auth_res = session.post(BASE_URL, data=AUTH_DATA, headers=HEADERS)
    soup = BeautifulSoup(auth_res.text, "html.parser")
    sessid = soup.find("input", {"name": "sessid"})["value"]
    return sessid


def start_workday(session):
    query['action'] = "open"
    pause_res = session.post(BASE_URL + TIMEMAN_ROUTE, data=FORM_DATA, params=query, headers=HEADERS)


def pause_workday(session):
    query['action'] = "pause"
    pause_res = session.post(BASE_URL + TIMEMAN_ROUTE, data=FORM_DATA, params=query, headers=HEADERS)


def continue_workday(session):
    query['action'] = "reopen"
    FORM_DATA['newActionName'] = "continues"
    con_res = session.post(BASE_URL + TIMEMAN_ROUTE, data=FORM_DATA, params=query, headers=HEADERS)


def close_workday(session):
    query['action'] = "close"
    con_res = session.post(BASE_URL + TIMEMAN_ROUTE, data=FORM_DATA, params=query, headers=HEADERS)


def check_alive(session):
    if is_alive():
        print("Bitrix24 seems to be alive")
    else:
        print("Sorry, its dead")


def show_help():
    print("""Bitrix24 Timeman CLI for lazy people with brains
Author: Vladimir Krasnov <v@krsnv.ru>

Usage: b24timeman-cli <action>

start      Start workday
close      End workday
pause      Make a break in workday
continue   Reopen workday or continue after break
check      Check Bitrix service is alive
""")


# Whole magic starts here
if __name__ == "__main__":

    try:
        cmds = sys.argv[1]
    except IndexError:
        show_help()
        quit()

    # Create session for future authorization and cookies
    session = requests.Session()

    # Query params for action request
    query = {
        "action": None, # open, close, pause, reopen
        "site_id": "s1",
        # Authorize with user login and pass. Getting sessid for valid forms
        "sessid": auth(session),
    }

    actions = {
        "start": start_workday,
        "close": close_workday,
        "pause": pause_workday,
        "continue": continue_workday,
        "check": check_alive,
        "help": show_help
    }

    def call_action():
       action = sys.argv[1]
       func = actions.get(action, lambda: print("Invalid action name. Type <help> for actions."))
       return func(session)

    call_action()

