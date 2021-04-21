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
                document.getElementsByClassName('register')[0].style.display = 'none'
                document.getElementsByClassName('balances')[0].style.display = ''
                document.getElementsByClassName('generators')[0].style.display = ''
                reload(response.data)
            }
            else {
                alert(response.message)
            }
        })
}

function normalize (n) {
    if (n.lt('1e5')) return n.toFixed(0)
    else return n.toExponential()
}

function reload (d) {
    console.log(d)
    data['balances'] = {}
    data['balances']['coins'] = new BigNumber(d['balances']['coins'])
    data['balances']['gold'] = new BigNumber(d['balances']['gold'])
    data['generators'] = []
    for (let i = 0; i < 3; i += 1) {
        data['generators'][i] = {
            'amount': new BigNumber(d['generators'][i]['amount']),
            'mult': new BigNumber(d['generators'][i]['mult'])
        }
    }
    data['mult'] = new BigNumber(d['mult'])
    data['xp'] = new BigNumber(d['xp'])

    document.getElementById('balance-coins').textContent = normalize(data['balances']['coins'])
    for (let i = 0; i < 3; i += 1) {
        console.log(data['generators'][0]['amount'])
        document.getElementById('generator' + (i + 1) + '-amount').textContent = normalize(data['generators'][0]['amount'])
        document.getElementById('generator' + (i + 1) + '-mult').textContent = normalize(data['generators'][0]['mult'])
        document.getElementById('generator' + (i + 1) + '-producing').textContent = normalize(data['generators'][0]['amount'].times(data['generators'][0]['mult']).times(data['mult']))
        document.getElementById('generator' + (i + 1) + '-cost').textContent = normalize((10 ** (i * 2 + 1)) * 1.1 ** data['generators'][i]['amount'])
    }
}

function purchaseGenerator (i) {
    let username = window.localStorage['_incremental_online_username']
    let password = window.localStorage['_incremental_online_password']
    fetch('http://localhost:1337/purchasegenerator?username=' + username + '&password=' + password + '&index=' + i)
        .then(response => response.json())
        .then(response => {
            if (response.success) {
                reload(response.data)
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
