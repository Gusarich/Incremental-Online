from flask import Flask, request
from hashlib import sha256
from string import ascii_letters, digits, punctuation
from time import time
import json
import sqlite3


app = Flask(__name__)
#cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

con = sqlite3.connect('db.sqlite', check_same_thread=False)
cur = con.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS Users (
    username TEXT PRIMARY KEY,
    password_hash TEXT,
    last_time INTEGER,
    game_data TEXT
)""")

CHARS = set(ascii_letters + digits)
GAME_DATA = json.dumps({
    'balances': {
        'coins': 10,
        'gold': 0
    },
    'xp': 0,
    'mult': 1,
    'generators': [{'amount': 0, 'bought': 0, 'mult': 1}, {'amount': 0, 'bought': 0, 'mult': 1}, {'amount': 0, 'bought': 0, 'mult': 1}]
})
TICKSPEED = 10


def hash(s):
    return sha256(s.encode()).hexdigest()


def timestamp():
    return int(time() * 1000)


def response(success, message=None, data=None, timestamp_=None):
    if success:
        return json.dumps({
            'success': 1,
            'timestamp': timestamp_,
            'data': data
        })
    else:
        return json.dumps({
            'success': 0,
            'message': message
        })


def str_check(s, chars=''):
    return set(s) <= CHARS | set(chars)


def calculate(username):
    user = cur.execute(f"SELECT * FROM Users WHERE username = '{username}'").fetchone()
    last_time, game_data = user[2], user[3]
    d = json.loads(game_data)
    gs = d['generators']

    t = int((timestamp() - last_time) / (1000 / TICKSPEED))

    if t > 250000:
        tick_mult = t / 250000
        t = 250000
    else:
        tick_mult = 1

    t = timestamp()

    while last_time < t:
        d['balances']['coins'] += (gs[0]['amount'] * gs[0]['mult'] * d['mult']) / TICKSPEED * tick_mult
        for i in range(1, len(gs)):
            gs[i - 1]['amount'] += (gs[i]['amount'] * gs[i]['mult']) / TICKSPEED * tick_mult
        last_time += 1000 // TICKSPEED
        t = timestamp()

    cur.execute(f"""UPDATE Users SET
                    last_time = {t},
                    game_data = '{json.dumps(d)}'
                    WHERE username = '{username}'""")

    return d, t


@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/register', methods=['GET'])
def register_route():
    username = request.args.get('username', '')
    password = request.args.get('password', '')

    if not 5 <= len(username) <= 12:
        return response(success=False, message='username length must be 5-12')
    if len(password) < 8:
        return response(success=False, message='password length must be 8+')
    if not str_check(username, '_'):
        return response(success=False, message='username must contain only [a-Z0-9]')
    if not str_check(password, punctuation):
        return response(success=False, message='password must contain only [a-Z0-9]')
    if cur.execute(f"""SELECT username FROM Users WHERE
                       username = '{username}'""").fetchone():
        return response(success=False, message='username already exists')

    # all good
    try:
        cur.execute(f"""INSERT INTO Users VALUES (
            "{username}",
            "{hash(password)}",
            {timestamp()},
            '{GAME_DATA}'
        )""")
    except Exception as e:
        print(e)
        return response(success=False, message='unknown error')

    data, timestamp_ = calculate(username)
    return response(success=True, data={'registered': True}, timestamp_=timestamp_)


@app.route('/calculate', methods=['GET'])
def calculate_route():
    username = request.args.get('username', '')
    password = request.args.get('password', '')

    if not cur.execute(f"""SELECT password_hash FROM Users WHERE
                           username = '{username}' AND
                           password_hash = '{hash(password)}'""").fetchone():
        return response(success=False, message='wrong username or password')

    data, timestamp_ = calculate(username)
    return response(success=True, data=data, timestamp_=timestamp_)


@app.route('/purchasegenerator', methods=['GET'])
def purchasegenerator_route():
    username = request.args.get('username', '')
    password = request.args.get('password', '')
    index = request.args.get('index', '-1')

    if not index.isdigit() or int(index) < 0 or int(index) > 2:
        return response(success=False, message='wrong index')

    index = int(index)

    if not cur.execute(f"""SELECT password_hash FROM Users WHERE
                           username = '{username}' AND
                           password_hash = '{hash(password)}'""").fetchone():
        return response(success=False, message='wrong username or password')

    data, timestamp_ = calculate(username)

    generator = data['generators'][index]

    if data['balances']['coins'] < (10 ** (index * 2 + 1)) * 1.1 ** generator['bought']:
        return response(success=False, message='not enough coins')

    data['balances']['coins'] -= (10 ** (index * 2 + 1)) * 1.1 ** generator['bought']
    generator['amount'] += 1
    generator['bought'] += 1
    data['xp'] += 1 * data['mult']

    cur.execute(f"""UPDATE Users SET
                    game_data = '{json.dumps(data)}'
                    WHERE username = '{username}'""")

    data, timestamp_ = calculate(username)
    return response(success=True, data=data, timestamp_=timestamp_)


if __name__ == '__main__':
    app.run('127.0.0.1', port=1337)
