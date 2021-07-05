#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import json
import telebot
import matplotlib.pyplot as plt
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import requests
from random import randint
import os
from datetime import date
from deputadoF import DeputadoF
from senador import Senador
import seaborn as sns
import seaborn_image as isns
import pandas as pd
import numpy as np



token = ""
DF = {}
S = {}
bot = telebot.TeleBot(token, parse_mode='MARKDOWN')
filename = './tmp.png'
log_filename = './logfiles/log.json'

log_dict = {}

def load_log():
    if(not os.path.exists(log_filename)):
        print("Arquivo nao existe")
        log_ = {}
        log_['commands'] = {}
        log_['consultas'] = {}
        with open(log_filename, 'w') as outfile:
            json.dump(log_dict, outfile)
    else:
        print("Arquivo existe")
        with open(log_filename,) as outfile:
            log_ = json.load(outfile)
    return log_

def savelog(command, consult = ''):
    print(command)
    if(not command in log_dict['commands']):
        print('Create: ' + command)
        log_dict['commands'][command] = 1
    else:
        log_dict['commands'][command] += 1
        print('Update: ' + command + ' ' + str(log_dict['commands'][command]))

    if(len(consult) > 0):
        if(not consult in log_dict['consultas']):
            print('Create: ' + consult)
            log_dict['consultas'][consult] = 1
        else:
            log_dict['consultas'][consult] += 1
            print('Update: ' + consult + ' ' +str(log_dict['consultas'][consult]))
    with open(log_filename, 'w') as outfile:
        json.dump(log_dict, outfile)


def open_databases():
    filename_DF = './database/'+date.today().strftime('%m_%Y')+'_DeputadosF.json'
    filename_S = './database/'+date.today().strftime('%m_%Y')+'_Senadores.json'
    json_DF = open(filename_DF)
    json_S = open(filename_S)
    df = DeputadoF(json.load(json_DF))
    s = Senador(json.load(json_S))
    return df, s

def prepare_plot(data):
    keys = list(data.keys())
    vals = list(data.values())
    clas = ['A'] * len(keys)
    df = pd.DataFrame({'R$': vals, 'categoria':keys, 'class': clas})
    return df

def set_plot_config():
    sns.set()
    sns.color_palette("dark")
    plt.style.use("seaborn-dark")
    for param in ['figure.facecolor', 'axes.facecolor', 'savefig.facecolor']:
        plt.rcParams[param] = '#212946'  # bluish dark grey

    for param in ['text.color', 'axes.labelcolor', 'xtick.color', 'ytick.color']:
        plt.rcParams[param] = '0.9'  # very light grey

def plot_photo(axs, element):
    img = Image.open(requests.get(element['foto'], stream=True).raw)
    axs.set_title(element['nome'], fontweight='bold', size=20)
    axs.grid(None)
    axs.axis('off')
    axs.imshow(img.transpose(Image.ROTATE_180))

def plot_graph(axs, element):
    if(len(element['despesa_categ']) > 0):
        df = prepare_plot(element['despesa_categ'])
        g = sns.barplot(data=df, y='R$',x='class', hue='categoria', ax=axs,  alpha=0.9)
        axs.set_title("Gastos no mês (em R$): "+ element['datadado'].split('-',1)[1], fontweight='bold', size=14)
        axs.grid(color='#2A3459')
        axs.set_ylabel('')
        axs.axes.get_xaxis().set_visible(False)
        #axs.axes.get_yaxis().set_visible(False)
        plt.subplots_adjust(top=0.95, bottom=0.24)
        for p in axs.patches:
            axs.annotate("%.2f" % p.get_height(), (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='center', fontsize=11, color='lightgray', xytext=(0.1, 5),
                textcoords='offset points')
        g.legend(loc='lower center', bbox_to_anchor=(0.48, -0.46))
    else:
         axs.axes.get_yaxis().set_visible(False)
         axs.axes.get_xaxis().set_visible(False)
         axs.set_title("Gastos no mês (em R$): "+ element['datadado'].split('-',1)[1], fontweight='bold', size=14)
         axs.text(0.5, 0.5, "Sem gastos declarados ainda", size=20,
         ha="center", va="center",
         bbox=dict(boxstyle="round",
                   ec=(1., 0.5, 0.5),
                   fc=(1., 0.8, 0.8),
                   ), color='red'
         )

def plot(element):
        fig, axs = plt.subplots(nrows=2, gridspec_kw={'height_ratios':[0.7,1]})
        fig = plt.gcf()
        fig.set_size_inches(5, 8, forward=True)
        plot_photo(axs[0], element)
        plot_graph(axs[1], element)
        for ax in axs:
            ax.set_anchor('C')
        #plt.show()
        fig.savefig(filename, format='png')
        image = Image.open(filename)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype('./font/arial.ttf', 40)
        draw.text((0, 0), "@AleteiaGov_bot", (116, 148, 242), font=font)
        image.save(filename)

def send_data(element, message):
    comp = ''
    if('cpf' in element):
            prof = ''
            for i in element['profissoes']:
                prof += i + " "
            comp = '*Escolaridade:* '+str(element['escolaridade'])+'\n'+\
                   '*Cpf:* '+str(element['cpf'])+'\n'+\
                   '*Profissões:* '+prof +'\n'+\
                    '*Condição Eleitoral:* '+str(element['condicao_eleitoral']) + '\n'

    text = '*Nome:* '+ str(element['nome'])+'\n'+\
          '*sexo:* '+ str(element['sexo'])+'\n'+\
          comp +\
          '*Partido:* '+str(element['partido'])+'\n'+\
          '*UF:* '+str(element['uf'])+'\n'+\
          '*Salario Líquido: R$* '+str(element['remuneracao'])+'\n'+\
          '*Auxilios: R$* '+str(element['aux_e_suplement'])+'\n'+\
          '*Despesa de Gabinete: R$* '+str(round(element['despesa_total']))+'\n'+\
          'Ficou insatisfeito com os gastos? Mande um email para ele: \n'+element['email'] +'\n'+\
          'Ou ligue para o gabinete: '+element['telefone']
          #TODO
    bot.reply_to(message, text)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    savelog('start')
    bot.reply_to(message, "Gostaria de stalkear um Deputado Federal ou um Senador? Use os comandos:\n"+\
        "\n- Gastos e infos: \n/deputado <NOME> ou /senador <NOME>\n"+\
        "\n- Lista de deputados: \n/deputadoLista <SIGLAPARTIDO>\n"+\
        "\n- Lista de senadores: \n/senadorLista <SIGLAPARTIDO>\n"+\
        "\n- Deputado mais gastão: \n/deputadoGastao\n"+\
        "\n- Senador mais gastão: \n/senadorGastao\n"+\
        "\n- Deputados que estão sem gastos declarados: \n/deputadoZerado\n"+\
        "\n- Senadores que estão sem gastos declarados: \n/senadorZerado\n" +\
        "\n- Partidos com deputados ativos: \n/deputadoPartidos\n"+\
        "\n- Partidos com senadores ativos: \n/senadorPartidos")

@bot.message_handler(commands=['deputadoLista','senadorLista'])
def lista_deputado (message):
        text = message.text
        partido = message.text.split(" ")
        if('senador' in text):
            savelog('senadorLista', partido)
            if(len(partido)>1):
                print(partido[1])
                names = S.list(partido[1])
            bot.reply_to(message, 'Senadores:\n' + names)
        else:
            savelog('deputadoLista', partido)
            if(len(partido)>1):
                print(partido[1])
                names = DF.list(partido[1])
            bot.reply_to(message, 'Deputados Federais:\n' + names)

@bot.message_handler(commands=['deputado', 'senador'])
def consulta (message):
    text = message.text
    if('senador' in text):
        name = text.replace("/senador ", "")
        savelog('senador', name)
        data = S.search(name)
    else:
        name = text.replace("/deputado ", "")
        savelog('deputado', name)
        data = DF.search(name)
    if(data):
        print(data)
        send_data(data, message)
        plot(data)
        with open(filename, 'rb') as f:
            contents = f.read()
            bot.send_photo(message.chat.id, photo=contents)
        os.remove(filename)
        return
    bot.reply_to(message, 'Ele não é deputado Federal')

@bot.message_handler(commands=['deputadoGastao', 'senadorGastao'])
def gastao (message):
    text = message.text
    if('senador' in text):
        savelog('senadorGastao')
        name = text.replace("/senador ", "")
        data = S.gastao()
    else:
        savelog('deputadoGastao')
        name = text.replace("/deputado ", "")
        data = DF.gastao()
    print(data)
    send_data(data, message)
    plot(data)
    with open(filename, 'rb') as f:
        contents = f.read()
        bot.send_photo(message.chat.id, photo=contents)
    os.remove(filename)
    return

@bot.message_handler(commands=['deputadoZerado', 'senadorZerado'])
def zerados(message):
    text = message.text
    if('senador' in text):
        savelog('senadorZerado')
        name = text.replace("/senador ", "")
        data = S.zerados()
    else:
        savelog('deputadoZerado')
        name = text.replace("/deputado ", "")
        data = DF.zerados()
    print(data)
    send_data(data, message)
    plot(data)
    with open(filename, 'rb') as f:
        contents = f.read()
        bot.send_photo(message.chat.id, photo=contents)
    os.remove(filename)
    return

@bot.message_handler(commands=['deputadoPartidos', 'senadorPartidos'])
def lista_partidos (message):
    text = message.text
    if('senador' in text):
        savelog('senadorPartidos')
        partidos = S.partidos()
        bot.reply_to(message, 'Senadores:\n' + partidos)
    else:
        savelog('deputadoPartidos')
        partidos = DF.partidos()
        bot.reply_to(message, 'Deputados Federais:\n' + partidos)

log_dict = load_log()
set_plot_config()
DF, S = open_databases()
DF_spend_categ = DF.get_categ_spend()
S_spend_categ = S.get_categ_spend()
print(DF.gastao())
#plot(S.search('Acir Gurgacz'))
#plot(DF.search('Tiririca'))
bot.polling()
