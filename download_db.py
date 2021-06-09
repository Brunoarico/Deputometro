#!/usr/bin/env python
#-*- coding: utf-8 -*-

import requests
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import date
from bs4 import BeautifulSoup
import re

header = { 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.90 Safari/537.36' }
url = "https://dadosabertos.camara.leg.br/api/v2/deputados/"

url_page = "https://www.camara.leg.br/deputados/"

get_remuneracao ="/remuneracao-deputado-detalhado?mesAno="

data = {}

phone = re.compile(r'(\(?\d{2}\)?\s)?(\d{4,5}\-\d{4})')

decimal = re.compile(r'\d+\.\d+\,\d+')

def get_data_from_page(id, MM, YY):
    remun = True
    auxilio = False
    aux = 0
    salario = "Sem Dados"
    tel = "(XX) XXXX-XXXX"
    page = requests.get(url_page + str(id))
    soup = BeautifulSoup(page.text, 'html.parser')
    for li_tag in soup.find_all('ul', {'class':'informacoes-deputado'}):
        for span_tag in li_tag.find_all('li'):
            if(not span_tag.text.find("Telefone")):
                print(phone.findall(span_tag.text)[0][0]+phone.findall(span_tag.text)[0][1])
                tel = phone.findall(span_tag.text)[0][0]+phone.findall(span_tag.text)[0][1]
                break
    if(MM <= 9):
        MM = str(MM).zfill(2)
    else:
        MM = str(MM)
    page = requests.get(url_page + str(id)+ get_remuneracao + MM + str(YY))
    print(url_page + str(id)+ get_remuneracao + MM + str(YY))
    soup = BeautifulSoup(page.text, 'html.parser')
    for li_tag in soup.find_all('table', {'class':'table table-striped table-bordered col-md-12'}):
        for span_tag in li_tag.find_all('tr'):
            #print(span_tag.text)
            if('a - Remuneração após Descontos Obrigatórios' in span_tag.text and remun):
                text = decimal.findall(span_tag.text)
                if(len(text) and float(text[0].replace(".","").replace(",","."))):
                    #print (float(text[0].replace(".","").replace(",",".")))
                    salario = float(text[0].replace(".","").replace(",","."))
                    remun = False
                    auxilio = True

            if('b - Auxílios' in span_tag.text and auxilio):
                text = decimal.findall(span_tag.text)
                if(len(text) and float(text[0].replace(".","").replace(",","."))):
                    #print (float(text[0].replace(".","").replace(",",".")))
                    aux = float(text[0].replace(".","").replace(",","."))
                    auxilio = False

    return (tel, salario, aux)



def get_id_name (MM, YY):
    r = requests.get(url, headers=header)
    if (r.status_code == 200):
        y = r.json()
        for i in y['dados'] :
            (t, s, a) = get_data_from_page(i['id'], MM, YY)
            data[i['id']] = {'nome': i['nome'], 'partido': i['siglaPartido'], 'uf':i['siglaUf'], 'foto':i['urlFoto'], 'email': i['email'], 'telefone': t, 'salario': s, 'auxilio': a}

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


today = date.today()
get_id_name (today.month-1, today.year)

for i in data:
    get_occup(i)
    get_spend_for (i, today.month-1 , today.year)

print(json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False))
with open('data.json', 'w') as outfile:
    json.dump(data, outfile)
