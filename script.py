import requests
#import fake_useragent
from bs4 import BeautifulSoup as b

URL = 'https://REMOVED/api_share/get_auth'

header = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0"
}

data = {
    '_token': 'j4fu1OhgXKccxqCOGBUhVeaSNXVkY7Xl3b9yia2Y',
    'value_1': 'REMOVED',
    'value_2': 'REMOVED',
    'value_4': '1',
    'value_5': 'Win32'
}

s = requests.Session()
s.headers.update(header)
responce = requests.post(URL, data=data, headers=header)
print(responce.headers)