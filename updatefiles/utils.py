import requests

def get_page (url, type):
    header = { 'Accept': 'application/'+type, 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.90 Safari/537.36' }
    r = requests.get(url, headers=header)
    if (r.status_code == 200):
        return r
    else:
        print('Erro ao consultar: ' + url, r.status_code)
        return ""
