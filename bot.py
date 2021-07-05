#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import json
import telebot
from matplotlib import pyplot as plt
from PIL import Image
import requests
from random import randint
import os
import datetime as date

plt.style.use('ggplot')
token = ""
data = {}

with open('data.json') as json_file:
    data = json.load(json_file)

bot = telebot.TeleBot(token, parse_mode='MARKDOWN')

def get_date():
    d = data['date']
    date_time_obj = date.datetime.strptime(d, '%d-%m-%Y')
    return str(date_time_obj.month) +"/"+ str(date_time_obj.year)

def addlabels(x,y):
    for i in range(len(x)):
        plt.text(i, y[i]+50, round(y[i]), ha = 'center')

def break_string(str):
    tokens = str.split(" ")
    n_tokens = len(tokens)
    new_str = ""

    for i in range(len(tokens)):
        new_str += tokens[i]
        print(i, n_tokens/2)
        if(i == n_tokens//2):
            new_str += "\n"
        else:
            new_str += " "
    print(new_str)
    return new_str

def send_data(deput, message):
    prof = ''
    for i in deput['profissoes']:
        prof += i + " "
    bot.reply_to(message, '*Nome:* '+ str(deput['nome'])+'\n'+\
                          '*Partido:* '+ str(deput['partido'])+'\n'+\
                          '*UF:* '+ str(deput['uf'])+'\n'+\
                          '*Profissões:* '+ prof+'\n'+\
                          '*Salario Líquido: R$* '+ str(deput['salario']) +'\n'+\
                          '*Auxilios: R$* '+ str(deput['auxilio']) +'\n'+\
                          '*Despesa de Gabinete: R$* '+ str(round(deput['Despesa_total'])) + '\n'
                          'Ficou insatisfeito com os gastos? Mande um email para ele: \n' + deput['email'] + '\n'
                          'Ou ligue para o gabinete: ' + deput['telefone'])

def gen_plot(deput):
    valores = deput['Despesa_categ']
    get_date()
    if(len(valores) > 0):
        #Plot da Foto
        fig, axs = plt.subplots(2,  gridspec_kw={'height_ratios':[1,2]})
        img = Image.open(requests.get(deput['foto'], stream=True).raw)
        axs[0].set_title(deput['nome'])
        axs[0].grid(None)
        axs[0].axis('off')
        axs[0].imshow(img)

        #Plot dados
        desc = list(valores.keys())
        cor = []
        for i in range(len(desc)):
            cor.append('#%06X' % randint(0, 0xFFFFFF))
            desc[i] = break_string(desc[i])

        value = list(valores.values())
        addlabels(desc, value)
        axs[1].set_title("Gastos no mês: "+ get_date())
        axs[1].grid(True)
        print(desc)
        for d, v, c in zip(desc, value, cor):
            axs[1].bar(d, v, color = c, label = d)
        axs[1].set_ylabel('R$')
        axs[1].axes.get_xaxis().set_visible(False)

        fig.subplots_adjust(bottom=0.35, wspace=0.3, hspace=0.3)

        plt.legend(loc='upper center', ncol=2,
                 bbox_to_anchor=(0.48, -0.1),fancybox=False, shadow=False, fontsize='small')

    else:
         fig, axs = plt.subplots(2)
         img = Image.open(requests.get(deput['foto'], stream=True).raw)
         axs[0].set_title(deput['nome'])
         axs[0].grid(None)
         axs[0].axis('off')
         axs[0].imshow(img)
         axs[1].axes.get_xaxis().set_visible(False)
         axs[1].axes.get_yaxis().set_visible(False)
         axs[1].set_title("Gastos no mês: "+get_date())
         axs[1].text(0.5, 0.5, "Sem Gastos Declarados", size=20,
         ha="center", va="center",
         bbox=dict(boxstyle="round",
                   ec=(1., 0.5, 0.5),
                   fc=(1., 0.8, 0.8),
                   )
         )

    fig.savefig("./teste.png", format='png')

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Gostaria de stalkear um Deputado Federal?"+\
                          "\nPara descobrir gastos e infos: /deputado <NOME>"+\
                          "\nPara lista de deputados: /lista <PARTIDO>"+\
                          "\nPara o mais gastão: /gastao"+\
                          "\nPara os que estão sem gastos declarados: /zeradinhos")

@bot.message_handler(commands=['gastao'])
def gastao (message):
    max = 0
    gast = 0
    for i in data:
        if(not '-' in data[i]):
            if(max < data[i]['Despesa_total']):
                max = data[i]['Despesa_total']
                gast = data[i]

    send_data(gast, message)
    gen_plot(gast)
    with open("./teste.png", 'rb') as f:
        contents = f.read()
        bot.send_photo(message.chat.id, photo=contents)
    os.remove("./teste.png")


@bot.message_handler(commands=['deputado'])
def consulta_deputado (message):
    name = message.text.replace("/deputado ", "")
    for i in data:
        if(not '-' in data[i]):
            if(data[i]['nome'].lower() == name.lower()):

                print(data[i])
                gen_plot(data[i])
                send_data(data[i], message)
                with open("./teste.png", 'rb') as f:
                    contents = f.read()
                    bot.send_photo(message.chat.id, photo =contents)
                os.remove("./teste.png")
                return

    bot.reply_to(message, 'Ele não é deputado')

@bot.message_handler(commands=['zeradinhos'])
def consulta_deputado (message):
    zer = ''
    for i in data:
        if(not '-' in data[i]):
            if(data[i]['Despesa_total'] == 0):
                zer += data[i]['nome'] +' ['+data[i]['partido']+']'+ '\n'
    bot.reply_to(message, 'Quem não tem gastos declarados são:\n' + zer)

@bot.message_handler(commands=['lista'])
def consulta_deputado (message):
    part = message.text.replace("/lista ", "").upper()
    d = ''
    for i in data:
        if(not '-' in data[i]):
            print(data[i]['partido'], part)
            if(data[i]['partido'] == part):
                d += data[i]['nome'] + ' [' + data[i]['partido'] + ' ]' + '\n'
    bot.reply_to(message, 'Deputados:\n' + d)

@bot.message_handler(commands=['gatao'])
def consulta_deputado (message):
    img = requests.get("https://s.glbimg.com/po/tt/f/original/2012/12/19/aristocat.jpg")
    bot.reply_to(message, "Por aqui não ha gatos, apenas gatunos")
    bot.send_photo(message.chat.id, photo =img.content)


bot.polling()
