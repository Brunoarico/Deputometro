import requests
import pandas as pd
import matplotlib.pyplot as plt
import json
from bs4 import BeautifulSoup
import re
from dateutil.relativedelta import relativedelta
from datetime import date
from utils import get_page

phone = re.compile(r'(\(?\d{2}\)?\s)?(\d{4,5}\-\d{4})')
decimal = re.compile(r'\d+\.\d+\,\d+')

class update_Deputados:
    def __init__(self):
        self.url_api = "https://dadosabertos.camara.leg.br/api/v2/deputados/"
        self.url_base = "https://www.camara.leg.br/deputados/"
        self.flags_remuneracao ="/remuneracao-deputado-detalhado?mesAno="
        self.data = {}
        self.lastmonth = date.today() - relativedelta(months=+2);
        self.last_month =  self.lastmonth.strftime('%m')


    def get_tel(self, id):
        tel = "(XX) XXXX-XXXX"
        url = self.url_base + str(id)
        text = get_page (url, 'text').text
        soup = BeautifulSoup(text, 'html.parser')
        for li_tag in soup.find_all('ul', {'class':'informacoes-deputado'}):
            for span_tag in li_tag.find_all('li'):
                if(not span_tag.text.find("Telefone")):
                    tel = phone.findall(span_tag.text)[0][0]+phone.findall(span_tag.text)[0][1]
                    break
        return tel


    def get_remuneration(self, id):
        remun_flag = True
        auxilio_flag = False
        aux = 0
        salario = "Sem Dados"
        url = self.url_base + str(id)+ self.flags_remuneracao + self.last_month + str(self.lastmonth.year)
        print(url)
        text = get_page (url, 'text').text
        soup = BeautifulSoup(text, 'html.parser')
        for li_tag in soup.find_all('table', {'class':'table table-striped table-bordered col-md-12'}):
            for span_tag in li_tag.find_all('tr'):
                if('a - Remuneração após Descontos Obrigatórios' in span_tag.text and remun_flag):
                    text = decimal.findall(span_tag.text)
                    if(len(text) and float(text[0].replace(".","").replace(",","."))):
                        salario = float(text[0].replace(".","").replace(",","."))
                        remun_flag = False
                        auxilio_flag = True

                if('b - Auxílios' in span_tag.text and auxilio_flag):
                    text = decimal.findall(span_tag.text)
                    if(len(text) and float(text[0].replace(".","").replace(",","."))):
                        aux = float(text[0].replace(".","").replace(",","."))
                        auxilio_flag = False

        return (salario, aux)

    def get_occup(self, id):
        occups = []
        url = self.url_api + str(id) + "/profissoes"
        resp = get_page (url, 'json').json()
        for i in resp["dados"]:
            if(i["titulo"] is not None):
                occups.append(i["titulo"])
        return occups

    def get_basics(self, id):
        basic = {}
        url = self.url_api + str(id)
        resp = get_page (url, 'json').json()
        i = resp['dados']
        basic['cpf'] = i['cpf']
        basic['escolaridade'] = i['escolaridade']
        basic['sexo'] = i['sexo'].replace('M', 'Masculino').replace('F', 'Feminino')
        basic['condicao_eleitoral'] = i['ultimoStatus']['condicaoEleitoral']
        return basic

    def get_spend_for (self, id):
            url = self.url_api + str(id) + "/despesas?ano=" + str(self.lastmonth.year) +" &mes=" + self.last_month + "&ordem=ASC&ordenarPor=ano"
            sum = 0
            dict_despesas = {}
            resp = get_page(url, 'json').json()
            for i in resp["dados"]:
                tipo = i["tipoDespesa"]
                valor = float(i["valorDocumento"])
                if(not tipo in dict_despesas):
                    dict_despesas[tipo] = valor
                else:
                    dict_despesas[tipo] += valor
                sum += valor
            return (sum, dict_despesas)

    def updateDataBase(self):
        dict = {}
        resp = get_page(self.url_api, 'json').json()
        for deputado in resp['dados'] :
            (s, a) = self.get_remuneration(deputado['id'])
            ocup = self.get_occup(deputado['id'])
            t = self.get_tel(deputado['id'])
            b = self.get_basics(deputado['id'])
            (sum, despesas) = self.get_spend_for(deputado['id'])
            self.data[str(deputado['id'])] = {'nome': deputado['nome'],
                                       'partido': deputado['siglaPartido'],
                                       'uf': deputado['siglaUf'],
                                       'foto': deputado['urlFoto'],
                                       'email': deputado['email'],
                                       'telefone': t,
                                       'remuneracao': s,
                                       'aux_e_suplement': a,
                                       'profissoes': ocup,
                                       'despesa_categ': despesas,
                                       'despesa_total': sum,
                                       'cpf': b['cpf'],
                                       'escolaridade': b['escolaridade'],
                                       'sexo': b['sexo'],
                                       'condicao_eleitoral': b['condicao_eleitoral']
                                       }
            print(self.data[str(deputado['id'])])
        dict["date"] = self.lastmonth.strftime("%d-%m-%Y")
        dict["deputados"] = self.data

        print(json.dumps(dict, indent=4, sort_keys=True, ensure_ascii=False))
        with open(date.today().strftime('%m_%Y')+'_DeputadosF.json', 'w') as outfile:
            json.dump(dict, outfile)




D = update_Deputados()
D.updateDataBase()
