function register () {
    let username = document.getElementById('username').value
    let password = document.getElementById('password').value
    fetch('http://localhost:1337/register?username=' + username + '&password=' + password)
        .then(response => response.json())
        .then(response => {
            if (response.success) {
                window.localStorage['_incremental_online_username'] = username
                window.localStorage['_incremental_online_password'] = password
                document.getElementsByClassName('register')[0].classList.add('hidden')
                document.getElementsByClassName('balances')[0].classList.remove('hidden')
                document.getElementsByClassName('gamefield')[0].classList.remove('hidden')
                document.getElementsByClassName('open-button')[0].classList.remove('hidden')
            }
            else {
                alert(response.message)
            }
        })
}

function login (alerted) {
    let username = document.getElementById('username').value
    let password = document.getElementById('password').value
    fetch('http://localhost:1337/calculate?username=' + username + '&password=' + password)
        .then(response => response.json())
        .then(response => {
            if (response.success) {
                window.localStorage['_incremental_online_username'] = username
                window.localStorage['_incremental_online_password'] = password
                reload(response.data, response.timestamp)
                tick()
                document.getElementsByClassName('register')[0].classList.add('hidden')
                document.getElementsByClassName('balances')[0].classList.remove('hidden')
                document.getElementsByClassName('gamefield')[0].classList.remove('hidden')
                document.getElementsByClassName('open-button')[0].classList.remove('hidden')
                setInterval(tick, 30)
            }
            else if (alerted) {
                alert(response.message)
            }
        })
}

function normalize (n) {
    if (n.lt('1e6')) return n.toFixed(0)
    else return n.toExponential(2)
}

function tick () {
    let timestamp = Date.now()
    let t = new BigNumber(timestamp).minus(data['last_tick']).div(1000)
    data['last_tick'] = timestamp

    data['balances']['coins'] = data['balances']['coins'].plus(data['generators'][0]['amount'].times(data['generators'][0]['mult']).times(data['mult']).times(t))

    for (let i = 1; i < 3; i += 1) {
        data['generators'][i - 1]['amount'] = data['generators'][i - 1]['amount'].plus(data['generators'][i]['amount'].times(data['generators'][i]['mult']).times(data['mult']).times(t))
    }

    document.getElementById('balance-coins').textContent = normalize(data['balances']['coins'])
    document.getElementById('balance-gold').textContent = normalize(data['balances']['gold'])

    for (let i = 0; i < 3; i += 1) {
        document.getElementById('generator' + (i + 1) + '-amount').textContent = normalize(data['generators'][i]['amount'])
        document.getElementById('generator' + (i + 1) + '-mult').textContent = normalize(data['generators'][i]['mult'])
        document.getElementById('generator' + (i + 1) + '-producing').textContent = normalize(data['generators'][i]['amount'].times(data['generators'][i]['mult']).times(data['mult']))
        document.getElementById('generator' + (i + 1) + '-cost').textContent = normalize((BigNumber(10).pow(i * 2 + 1)).times(BigNumber(1.1).pow(data['generators'][i]['bought'])))
    }
    for (let i = 0; i < 3; i += 1) {
        document.getElementById('upgrade' + (i + 1) + '-cost').textContent = normalize(data['upgrades'][i]['cost'].times(BigNumber(20).pow(data['upgrades'][i]['amount'])))
    }

    document.getElementById('xp-progressbar').textContent = 'Level up (' + normalize(data['xp']) + ' / ' + normalize(BigNumber(10).times(BigNumber(2).pow(data['level'].minus(1)))) + ')'
    document.getElementById('xp-progressbar').style.width = data['xp'].div(BigNumber(10).times(BigNumber(2).pow(data['level'].minus(1)))).times(100).toString() + '%'
}

function reload (d, timestamp) {
    data['balances'] = {}
    data['balances']['coins'] = new BigNumber(d['balances']['coins'])
    data['balances']['gold'] = new BigNumber(d['balances']['gold'])
    data['generators'] = []
    for (let i = 0; i < 3; i += 1) {
        data['generators'][i] = {
            'amount': new BigNumber(d['generators'][i]['amount']),
            'bought': new BigNumber(d['generators'][i]['bought']),
            'mult': new BigNumber(d['generators'][i]['mult'])
        }
    }
    data['upgrades'] = []
    for (let i = 0; i < 3; i += 1) {
        data['upgrades'][i] = {
            'amount': new BigNumber(d['upgrades'][i]['amount']),
            'cost': new BigNumber(d['upgrades'][i]['cost'])
        }
    }
    data['mult'] = new BigNumber(d['mult'])
    data['xp'] = new BigNumber(d['xp'])
    data['level'] = new BigNumber(d['level'])
    data['last_tick'] = timestamp
}

function purchaseGenerator (i) {
    let username = window.localStorage['_incremental_online_username']
    let password = window.localStorage['_incremental_online_password']
    fetch('http://localhost:1337/purchasegenerator?username=' + username + '&password=' + password + '&index=' + i)
        .then(response => response.json())
        .then(response => {
            if (response.success) {
                reload(response.data, response.timestamp)
            }
            else {
                alert(response.message)
            }
        })
}

function purchaseUpgrade (i) {
    let username = window.localStorage['_incremental_online_username']
    let password = window.localStorage['_incremental_online_password']
    fetch('http://localhost:1337/purchaseupgrade?username=' + username + '&password=' + password + '&index=' + i)
        .then(response => response.json())
        .then(response => {
            if (response.success) {
                reload(response.data, response.timestamp)
            }
            else {
                alert(response.message)
            }
        })
}

function openLeaderboard () {
    let username = window.localStorage['_incremental_online_username']
    let password = window.localStorage['_incremental_online_password']
    fetch('http://localhost:1337/leaderboard?username=' + username + '&password=' + password)
        .then(response => response.json())
        .then(response => {
            if (response.success) {
                reload(response.data['data'], response.timestamp)

                let lb = response.data['leaderboard']
                console.log(lb)
                if (lb.length < 10) m = lb.length
                else m = 10

                for (let i = 1; i <= m; i += 1) {
                    document.getElementById('leaderboard-' + i).textContent = lb[i - 1][0] + ' — ' + normalize(BigNumber(lb[i - 1][1])) + ' Coins'
                }
                if (lb.length > 10) {

                }

                document.getElementsByClassName('leaderboard')[0].style.display = ''
            }
            else {
                alert(response.message)
            }
        })
}

function closeLeaderboard () {
    document.getElementsByClassName('leaderboard')[0].style.display = 'none';
}

BigNumber.config({ ROUNDING_MODE: BigNumber.ROUND_FLOOR })
var data = {}

window.onload = () => {
    let w = document.getElementsByClassName('links')[0].clientWidth;
    w = w / 2;
    document.getElementsByClassName('links')[0].style.left = 'calc(50% - ' + w + 'px)'

    if (window.localStorage.getItem('_incremental_online_username') != null) {
        let username = window.localStorage.getItem('_incremental_online_username')
        let password = window.localStorage.getItem('_incremental_online_password')
        document.getElementById('username').value = username
        document.getElementById('password').value = password
        login(false)
    }
}
