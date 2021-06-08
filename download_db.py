#!/usr/bin/env python
#-*- coding: utf-8 -*-

import requests
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import date

header = { 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.90 Safari/537.36' }
url = "https://dadosabertos.camara.leg.br/api/v2/deputados/"

data = {}

def get_id_name ():
    r = requests.get(url, headers=header)
    if (r.status_code == 200):
        y = r.json()
        for i in y['dados'] :
            data[i['id']] = {'nome': i['nome'], 'partido': i['siglaPartido'], 'uf':i['siglaUf'], 'foto':i['urlFoto']}

def get_occup(id):
    query = "/profissoes"
    r = requests.get(url + str(id) + query, headers=header)

    if (r.status_code == 200):
        occups =[]
        y = r.json()
        for i in y["dados"]:
            if(i["titulo"] is not None):
                occups.append(i["titulo"])
        root = data[id]
        root['profissoes'] = occups
        print(root)

def get_spend_for (id, MM, YY):
        query = "/despesas?ano="+str(YY)+"&mes="+str(MM)+"&ordem=ASC&ordenarPor=ano"
        r = requests.get(url + str(id) + query, headers=header)
        sum = 0
        dict_despesas = {}
        if (r.status_code == 200):
            y = r.json()
            for i in y["dados"]:
                    tipo = i["tipoDespesa"]
                    valor = float(i["valorDocumento"])
                    if(not tipo in dict_despesas):
                        dict_despesas[tipo] = valor
                    else:
                        dict_despesas[tipo] += valor
                    sum += valor
            print(dict_despesas)
            root = data[id]
            root['Despesa_categ'] = dict_despesas
            root['Despesa_total'] = sum
        else:
            print("Error:" ,r.status_code, "fail request")
        return sum



get_id_name ()
today = date.today()
for i in data:
    get_occup(i)
    get_spend_for (i, today.month-1 , today.year)

print(json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False))
with open('data.json', 'w') as outfile:
    json.dump(data, outfile)
