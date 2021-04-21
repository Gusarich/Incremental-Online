function register () {
    let username = document.getElementById('username').value
    let password = document.getElementById('password').value
    fetch('http://localhost:1337/register?username=' + username + '&password=' + password)
        .then(response => response.json())
        .then(response => {
            if (response.success) {
                window.localStorage['_incremental_online_username'] = username
                window.localStorage['_incremental_online_password'] = password
                document.getElementsByClassName('register')[0].style.display = 'none'
                document.getElementsByClassName('balances')[0].style.display = ''
                document.getElementsByClassName('generators')[0].style.display = ''
            }
            else {
                alert(response.message)
            }
        })
}

function login () {
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
                document.getElementsByClassName('register')[0].style.display = 'none'
                document.getElementsByClassName('balances')[0].style.display = ''
                document.getElementsByClassName('generators')[0].style.display = ''
                setInterval(tick, 50)
            }
            else {
                alert(response.message)
            }
        })
}

function normalize (n) {
    if (n.lt('1e5')) return n.toFixed(0)
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
    for (let i = 0; i < 3; i += 1) {
        document.getElementById('generator' + (i + 1) + '-amount').textContent = normalize(data['generators'][i]['amount'])
        document.getElementById('generator' + (i + 1) + '-mult').textContent = normalize(data['generators'][i]['mult'])
        document.getElementById('generator' + (i + 1) + '-producing').textContent = normalize(data['generators'][i]['amount'].times(data['generators'][i]['mult']).times(data['mult']))
        document.getElementById('generator' + (i + 1) + '-cost').textContent = normalize((BigNumber(10).pow(i * 2 + 1)).times(BigNumber(1.1).pow(data['generators'][i]['bought'])))
    }
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
    data['mult'] = new BigNumber(d['mult'])
    data['xp'] = new BigNumber(d['xp'])
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

BigNumber.config({ ROUNDING_MODE: BigNumber.ROUND_FLOOR })
var data = {}

window.onload = () => {
    if (window.localStorage.getItem('_incremental_online_username') != null) {
        let username = window.localStorage.getItem('_incremental_online_username')
        let password = window.localStorage.getItem('_incremental_online_password')
        document.getElementById('username').value = username
        document.getElementById('password').value = password
        login()
    }
}
