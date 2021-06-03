import requests
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt

header = { 'Accept': 'application/xml', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.90 Safari/537.36' }
url = "https://dadosabertos.camara.leg.br/api/v2/deputados/"

dict = {}

def get_id_name ():
    r = requests.get(url, headers=header)
    if (r.status_code == 200):
        tree =  ET.ElementTree(ET.fromstring(r.content))
        root = tree.getroot()
        for child in  root.findall("dados"):
            for dep in child.findall("deputado_"):
                id = dep.find("id").text
                name = dep.find("nome").text
                dict[id] = name
    else:
        print("Error:" ,r.status_code, "fail request")

def get_occup(id):
    query = "/profissoes"
    r = requests.get(url + str(id) + query, headers=header)
    occ = []
    if (r.status_code == 200):
        tree =  ET.ElementTree(ET.fromstring(r.content))
        root = tree.getroot()
        for child in  root.findall("dados"):
            for dep in child.findall("profissao"):
                if(dep.find("titulo") is not None):
                    titulo = dep.find("titulo").text
                    occ.append(titulo)
                    print("Ocupacao:" + titulo + ", ",end ="")
                else:
                    print("Ocupacao: nenhum/nao declarado")
        print("")
        return occ


def get_spend_for (id, MM, YY):
        query = "/despesas?ano="+str(YY)+"&mes="+str(MM)+"&ordem=ASC&ordenarPor=ano"
        r = requests.get(url + str(id) + query, headers=header)
        sum = 0
        dict_despesas = {}
        if (r.status_code == 200):
            tree =  ET.ElementTree(ET.fromstring(r.content))
            root = tree.getroot()
            for child in  root.findall("dados"):
                for dep in child.findall("registroCotas"):
                    tipo = dep.find("tipoDespesa").text
                    valor = float(dep.find("valorDocumento").text)
                    if(not tipo in dict_despesas):
                        dict_despesas[tipo] = valor
                    else:
                        dict_despesas[tipo] += valor
                    sum += valor
            for i in dict_despesas:
                print(i, dict_despesas[i])
            print("Total:", sum)
        else:
            print("Error:" ,r.status_code, "fail request")
        return sum

get_id_name ()

value_dict = {}

for i in dict:
    print("------------------------------------------------------------------")
    print("Nome: ", dict[i], i)
    #get_occup(i)
    value_dict[dict[i]] = get_spend_for(i, 4 ,2021)
    print("------------------------------------------------------------------")

money = list(map(int, list(value_dict.values())))
names = list(value_dict.keys())


plt.barh(list(value_dict.keys()), list(value_dict.values()), align='center')


plt.show()
