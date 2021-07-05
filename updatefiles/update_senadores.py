#!/usr/bin/env python
#-*- coding: utf-8 -*-

import requests
import pandas as pd
import matplotlib.pyplot as plt
import json
from bs4 import BeautifulSoup
import re
from dateutil.relativedelta import relativedelta
from datetime import date
from utils import get_page
import pandas as pd
import io
from unidecode import unidecode


pd.set_option('display.max_rows', None)

class update_Senadores:
    def __init__(self):
        self.url_api = "https://legis.senado.leg.br/dadosabertos/senador/lista/atual"
        self.url_dados_id = 'https://www6g.senado.leg.br/transparencia/sen/'
        self.url_cons_remu = "http://www.senado.leg.br/transparencia/LAI/secrh/SF_ConsultaRemuneracaoServidoresParlamentares_"
        self.meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        self.list = {}
        self.lastmonth = date.today() - relativedelta(months=+1);
        self.last_month =  self.lastmonth.strftime('%m')
        self.ddd_brasilha = '(61)'

    def process_tel(self, t):
        beg = ''
        tels = ''
        for numbers in t:
            if(isinstance(numbers, dict)):
                beg = numbers['NumeroTelefone'][0:4]
                tels += numbers['NumeroTelefone'][4:8] + ' '
            else:
                if(numbers == 'NumeroTelefone'):
                    beg = t[numbers][0:4]
                    tels += t[numbers][4:8] + ' '
        return self.ddd_brasilha + ' ' + beg + '-' + tels.strip().replace(' ', ' / ')

    def get_senadores(self):

        resp = get_page(self.url_api, 'json').json()
        resp = resp['ListaParlamentarEmExercicio']['Parlamentares']
        id = ''
        for i in resp['Parlamentar']:
            basics = {}
            info = i['IdentificacaoParlamentar']
            id = info['CodigoParlamentar']
            basics['nome'] = info['NomeParlamentar']
            basics['sexo'] = info['SexoParlamentar']
            basics['foto'] = info['UrlFotoParlamentar']
            basics['site'] = info['UrlPaginaParlamentar']
            if('EmailParlamentar' in info):
                basics['email'] = info['EmailParlamentar']
            else:
                basics['email'] = 'Não tem email! Vê se pode!?'
            basics['partido'] = info['SiglaPartidoParlamentar']
            basics['uf'] = info['UfParlamentar']
            basics['telefone'] = self.process_tel(info['Telefones']['Telefone'])
            self.list[id] = basics



    def get_value_of_spend(self, id, param):
        resp = get_page(self.url_dados_id + id + "/"+ param, 'text').text
        soup = BeautifulSoup(resp, 'lxml')
        table = soup.find('table',{'class':'table table-striped'})
        if(table):
            tr = table.find_all('tr')
            for t in tr:
                a = t.find('a')
                if(a):
                    if(("mesAno="+self.last_month) in a['href']):
                        return float(t.find('span').contents[0].replace('.','').replace(',', '.'))
        return 0


    def get_spend_for(self, id):
        spent_dict = {}
        sum = 0
        resp = get_page(self.url_dados_id + id, 'text').text
        soup = BeautifulSoup(resp, 'lxml')
        tables = soup.find_all('div',{'class':'accordion-group accordion-caret'})
        for tb in tables:
            td_val = tb.find_all('td', {'class':'valor'})
            for v in td_val:
                a = v.find('a')
                if(a):
                    url_param = a['href'].split('#')[0]
                    value = 0
                    if(not '.pdf' in url_param):
                        value = self.get_value_of_spend(id, url_param)
                    if(value > 0):
                        spent_dict[a['title'].split(' de ', 1)[1]] = value
                        sum += value
                        #print(a['title'].split(' de ', 1)[1], value)
        return (spent_dict, sum)


    def get_remuneration(self):
        self.remunera = {}
        self.aux_sup = {}
        url = self.url_cons_remu + str(self.lastmonth.year) + self.last_month +'.csv'
        resp = get_page(url, 'csv').content
        file = resp.decode('latin-1').replace('\r', '').replace(' ', '')
        file = file.split("\n",1)[1] #remove cabecalho
        file = file.replace('GabinetedoSenador', '').replace('GabinetedaSenadora', '')
        frame = pd.read_csv(io.StringIO(file), delimiter=";", decimal=",")
        filtered = frame.loc[frame['VÍNCULO'] == 'PARLAMENTAR']
        filtered = filtered[['REM_LIQUIDA', 'AUXILIOS', 'LOTAÇÃOEXERCÍCIO', 'TIPOFOLHA']]
        filtered = filtered.sort_values(['LOTAÇÃOEXERCÍCIO'], ascending=True)
        for i in filtered.index:
            nome = unidecode(filtered['LOTAÇÃOEXERCÍCIO'][i]).lower()
            if(filtered['TIPOFOLHA'][i] == 'Normal'):
                self.remunera[nome] = filtered['REM_LIQUIDA'][i]
                if(not nome in self.aux_sup):
                    self.aux_sup[nome] = filtered['AUXILIOS'][i]
                else:
                    self.aux_sup[nome] += filtered['AUXILIOS'][i]
            else:
                if(not nome in self.aux_sup):
                    self.aux_sup[nome] = filtered['REM_LIQUIDA'][i]
                else:
                    self.aux_sup[nome] += filtered['REM_LIQUIDA'][i]

    def updateDataBase(self):
        dict = {}
        self.get_senadores()
        self.get_remuneration()
        for i in self.list:
            (categ, total) = self.get_spend_for(i)
            self.list[i]['despesa_categ'] = categ
            self.list[i]['despesa_total'] = total
            nome1 = unidecode(self.list[i]['email']).lower().replace('sen.', '').split('@')[0]
            nome2 = unidecode(self.list[i]['nome']).replace(' ', '')
            if(nome1 in self.remunera):
                self.list[i]['remuneracao'] = self.remunera[nome1]
                self.list[i]['aux_e_suplement'] = self.aux_sup[nome1]
            elif(nome2 in self.remunera):
                self.list[i]['remuneracao'] = self.remunera[nome2]
                self.list[i]['aux_e_suplement'] = self.aux_sup[nome2]
            else:
                self.list[i]['remuneracao'] = 'Sem dados na base'
                self.list[i]['aux_e_suplement'] = 'Sem dados na base'
            print(nome1)
            print(json.dumps(self.list[i], indent=4, sort_keys=True, ensure_ascii=False))
        dict["date"] = self.lastmonth.strftime("%d-%m-%Y")
        dict["senadores"] = self.list


        print(json.dumps(dict, indent=4, sort_keys=True, ensure_ascii=False))
        with open(date.today().strftime('%m_%Y')+'_Senadores.json', 'w') as outfile:
            json.dump(dict, outfile)


S = update_Senadores()
S.updateDataBase()
