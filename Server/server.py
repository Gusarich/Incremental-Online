from flask import Flask, request
from hashlib import sha256
from string import ascii_letters, digits, punctuation
from time import time
from math import log10
from random import randint
import json
import sqlite3


app = Flask(__name__)
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
        'coins': 500,
        'gold': 0
    },
    'xp': 0,
    'level': 1,
    'mult': 1,
    'generators': [{'amount': 0, 'bought': 0, 'mult': 1}, {'amount': 0, 'bought': 0, 'mult': 1}, {'amount': 0, 'bought': 0, 'mult': 1}],
    'upgrades': [{'amount': 0, 'cost': 300}, {'amount': 0, 'cost': 10000}, {'amount': 0, 'cost': 500000}],
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
    us = d['upgrades']

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

    while d['xp'] >= 10 * 2 ** (d['level'] - 1):
        d['xp'] -= 10 * 2 ** (d['level'] - 1)
        d['balances']['gold'] += d['level']
        d['level'] += 1

    cur.execute(f"""UPDATE Users SET
                    last_time = {t},
                    game_data = '{json.dumps(d)}'
                    WHERE username = '{username}'""")
    con.commit()

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
        con.commit()
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

    if not cur.execute(f"""SELECT password_hash FROM Users WHERE
                           username = '{username}' AND
                           password_hash = '{hash(password)}'""").fetchone():
        return response(success=False, message='wrong username or password')

    index = request.args.get('index', '-1')

    if not index.isdigit() or int(index) < 0 or int(index) > 2:
        return response(success=False, message='wrong index')

    index = int(index)

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
    con.commit()

    data, timestamp_ = calculate(username)
    return response(success=True, data=data, timestamp_=timestamp_)


@app.route('/purchaseupgrade', methods=['GET'])
def purchaseupgrade_route():
    username = request.args.get('username', '')
    password = request.args.get('password', '')

    if not cur.execute(f"""SELECT password_hash FROM Users WHERE
                           username = '{username}' AND
                           password_hash = '{hash(password)}'""").fetchone():
        return response(success=False, message='wrong username or password')

    index = request.args.get('index', '-1')

    if not index.isdigit() or int(index) < 0 or int(index) > 2:
        return response(success=False, message='wrong index')

    index = int(index)

    data, timestamp_ = calculate(username)

    upgrade = data['upgrades'][index]
    generator = data['generators'][index]

    if data['balances']['coins'] < upgrade['cost'] * 20 ** upgrade['amount']:
        return response(success=False, message='not enough coins')

    data['balances']['coins'] -= upgrade['cost'] * 20 ** upgrade['amount']
    upgrade['amount'] += 1
    generator['mult'] *= 2
    data['xp'] += 5 * data['mult']

    cur.execute(f"""UPDATE Users SET
                    game_data = '{json.dumps(data)}'
                    WHERE username = '{username}'""")
    con.commit()

    data, timestamp_ = calculate(username)
    return response(success=True, data=data, timestamp_=timestamp_)


@app.route('/leaderboard', methods=['GET'])
def leaderboard_route():
    username = request.args.get('username', '')
    password = request.args.get('password', '')

    if not cur.execute(f"""SELECT password_hash FROM Users WHERE
                           username = '{username}' AND
                           password_hash = '{hash(password)}'""").fetchone():
        return response(success=False, message='wrong username or password')

    data, timestamp_ = calculate(username)

    users = cur.execute('SELECT `username`, `game_data` FROM Users').fetchall()
    users = [(i, json.loads(j)['balances']['gold']) for i, j in users]
    users.sort(key=lambda u: u[1], reverse=True)
    i = [i[0] for i in users].index(username)
    if i >= 10:
        users = users[:10] + users[i]
    else:
        users = users[:10]

    resp = {'data': data, 'leaderboard': users}
    return response(success=True, data=resp, timestamp_=timestamp_)


@app.route('/prestige', methods=['GET'])
def prestige_route():
    username = request.args.get('username', '')
    password = request.args.get('password', '')

    if not cur.execute(f"""SELECT password_hash FROM Users WHERE
                           username = '{username}' AND
                           password_hash = '{hash(password)}'""").fetchone():
        return response(success=False, message='wrong username or password')

    data, timestamp_ = calculate(username)

    coins, gold = data['balances']['coins'], data['balances']['gold']
    data = json.loads(GAME_DATA)
    data['balances']['gold'] = gold + max(0, log10(coins / 1000000))

    cur.execute(f"""UPDATE Users SET
                    last_time = {timestamp_},
                    game_data = '{json.dumps(data)}'
                    WHERE username = '{username}'""")
    con.commit()

    return response(success=True, data=data, timestamp_=timestamp_)


@app.route('/dicebet', methods=['GET'])
def dicebet_route():
    username = request.args.get('username', '')
    password = request.args.get('password', '')

    if not cur.execute(f"""SELECT password_hash FROM Users WHERE
                           username = '{username}' AND
                           password_hash = '{hash(password)}'""").fetchone():
        return response(success=False, message='wrong username or password')

    chance = request.args.get('chance', 'a')
    amount = request.args.get('amount', 'a')

    if not (chance.isdigit() and amount.isdigit()):
        return response(success=False, message='chance and amount must be integers')

    chance = int(chance)
    amount = int(amount)

    if not 0 < chance < 100:
        return response(success=False, message='chance must be 1-99')

    data, timestamp_ = calculate(username)

    if amount < 1:
        return response(success=False, message='amount must be 1+')
    if amount > data['balances']['coins']:
        return response(success=False, message='not enough coins')

    rnd = randint(1, 100)
    if rnd <= chance:
        data['balances']['coins'] += amount * (100 / chance - 1) # win
    else:
        data['balances']['coins'] -= amount # lose

    data['xp'] += 2

    cur.execute(f"""UPDATE Users SET
                    last_time = {timestamp_},
                    game_data = '{json.dumps(data)}'
                    WHERE username = '{username}'""")
    con.commit()

    data, timestamp_ = calculate(username)

    return response(success=True, data=data, timestamp_=timestamp_)


if __name__ == '__main__':
    app.run('127.0.0.1', port=1337)
