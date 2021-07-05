from datetime import date
import json

class DeputadoF:
    def __init__(self, file):
        self.file = file

    def search(self, name):
        base = self.file['deputados']
        for i in base:
            if(base[i]['nome'] == name):
                base[i]['datadado'] = self.file['date']
                #print(base[i])
                return base[i]
        return {}

    def list(self, partido):
        names = ''
        base = self.file['deputados']
        for i in base:
            if(base[i]['partido'].upper() == partido.upper()):
                names += base[i]['nome'] + ' ('+base[i]['partido']+')\n'
        return names

    def get_categ_spend(self):
        s = set()
        base = self.file['deputados']
        for i in base:
            d = base[i]['despesa_categ']
            list_s = list(d.keys())
            list_s = [categ.lower().capitalize() for categ in list_s]
            s.update(list_s)
        return s

    def gastao(self):
        max = 0
        gast = 0
        base = self.file['deputados']
        for i in base:
            d = base[i]['despesa_total']
            if(max < d):
                max = d
                gast = base[i]
        gast['datadado'] = self.file['date']
        return gast

    def partidos(self):
        partidos = ''
        base = self.file['deputados']
        s = set()
        for i in base:
                s.update({base[i]['partido']})
        for i in s:
                partidos += i+'\n'
        return partidos

    def zerados(self):
        names = ''
        base = self.file['deputados']
        for i in base:
            if(base[i]['Despesa_total'] == 0):
                    names += base[i]['nome'] + ' ('+base[i]['partido']+')\n'
        return names
