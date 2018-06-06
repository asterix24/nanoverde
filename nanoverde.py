import string
import sys
import binascii
import serial
import datetime
import requests
import time
import os
from optparse import OptionParser
from time import strftime

class Led:
    def __init__(self):
        if not os.path.isdir("/sys/class/gpio/pioA27"):
            file = open("/sys/class/gpio/export", "w")
            file.write("27")
            file.close()
        if not os.path.isdir("/sys/class/gpio/pioA26"):
            file = open("/sys/class/gpio/export", "w")
            file.write("26")
            file.close()

        file = open("/sys/class/gpio/pioA27/direction", "w")
        file.write("out")
        file.close()
        file = open("/sys/class/gpio/pioA27/value", "w")
        file.write("0")
        file.close()

        file = open("/sys/class/gpio/pioA26/direction", "w")
        file.write("out")
        file.close()
        file = open("/sys/class/gpio/pioA26/value", "w")
        file.write("0")
        file.close()

    def __del__(self):
        file = open("/sys/class/gpio/pioA27/value", "w")
        file.write("0")
        file.close()
        file = open("/sys/class/gpio/unexport", "w")
        file.write("27")
        file.close()

        file = open("/sys/class/gpio/pioA26/value", "w")
        file.write("0")
        file.close()
        file = open("/sys/class/gpio/unexport", "w")
        file.write("26")
        file.close()

    def erogaCredito(self, sec):
        file = open("/sys/class/gpio/pioA27/value", "w")
        file.write("1")
        time.sleep(sec)
        file.write("0")
        file.close()

    def ledErrore(self, sec, count):
        file = open("/sys/class/gpio/pioA26/value", "w")
        for i in range(0, count):
            file.write("1")
            time.sleep(sec)
            file.write("0")
        file.close()


def controlloKey(key, utenti_dict):
    if key in utenti_dict:
        return utenti_dict[key]
    return None


def premioErogato(key):
    doc_dict = creazioneDizionario("documento")
    oggi = datetime.datetime.today()
    stoday = oggi.strftime("%y-%m-%d")
    stoday = "20"+stoday
    print(stoday)
    if key in doc_dict:
        return (stoday != doc_dict[key])

    return True


def verificaOreRegistrate(user):
    print(user)
    today = datetime.datetime.today()
    oneday = datetime.timedelta(days=4)
    day=datetime.timedelta(days=5)                                              
    v = today-day  # messo in modo che funzioni dato che oggi non e venerdi e ho
    l = v-oneday                                                                
    v = v.strftime("%y-%m-%d")                                                  
    l = l.strftime("%y-%m-%d")                                                  
    slunedi = "20"+str(l)                                                       
    svenerdi = "20"+str(v)                                           
    print("lunedi: "+slunedi+"venerdi: "+svenerdi)                   
    r = requests.get("https://showtime.develer.com/summary/" +       
                     user+"?from_date="+slunedi+"&to_date="+svenerdi)
    print(r.json)  # oggetto JSON                                    
    a = r.json()                                                     
    totaleOre = 0                                                    
    print (a, type(a))                                               
    for k, v in a.items():                                  
        v = str(v)                                                              
        v = v.split('.')                                                        
        ore = float(v[1])/60                                                    
        totaleOre = totaleOre+ore+float(v[0])                                   
    if totaleOre >= 35 and a[svenerdi] >= 6:                                    
        return True  

    return False


def registraPremioUtente(user):
    today = datetime.datetime.today()
    today = "20"+today.strftime("%y-%m-%d")
    print("RITIRARE PREMIO")  # EROGAZIONE PREMIO
    f = open('documento.txt', 'a')
    f.write(user+';'+str(today)+'\n')
    f.close()


def creazioneDizionario(nome):
    f = open(nome+'.txt', 'r')
    utenti_dict = {}
    for line in f:
        line = line.strip()
        try:
            if line != "":
                l = line.split(';')
                k = l[0].strip()
                v = l[1].strip()

                utenti_dict[k] = v
        except IndexError:
            continue

    return utenti_dict


def letturaTag():
    try:
        ser = serial.Serial("/dev/ttyS2", 9600)
    except IOError as e:
        print(e)
        sys.exit("Error connecting device")

    tag = ""
    startTag = False

    while True:
        c = ser.read(1)
        if startTag:
            tag += c
        if c == '\x02':
            startTag = True
        if c == '\x03':
            break
    if len(tag) == 15:
        tag = tag[:10]
        return tag
    return None

                                                                                
def erogazioneNonVenerdi():                                                  
    parser=OptionParser()                                                    
    parser.add_option("-v", action="store_true", dest="value", default=False)
    (options, args)=parser.parse_args()                                   
    return options.value                                                  
                                                                          
if __name__ == "__main__":                                                
    ven=erogazioneNonVenerdi()                                       
    print(ven)                                              
    timenow=strftime('%H:%M')                                                   
    l=Led()                                                                     
    if (datetime.date.today().weekday()==4 and timenow=="18:00") or (ven):      
        print("puoi eseguire")                                                  
                                                                                
        utenti_dict = creazioneDizionario("utenti")                          
        while True:                                                          
            key = letturaTag()                                               
            print(key)     

            utente = controlloKey(key, utenti_dict)                          
            if key is not None:                                                 
                if utente is not None:                                          
                    print("codice giusto")                                      
                    if premioErogato(utente):                                   
                        print("non hai ancora ritirato il premio")           
                        # chiedo al server per sapere se ha registrato le ore
                        lavoro = verificaOreRegistrate(utente)               
                                                                             
                        if lavoro:                                           
                            print("hai inserito tutte le ore ")              
                            l.erogaCredito(1)                                
                            registraPremioUtente(utente)                     
                            print("RITIRA PREMIO")                        
                        else:                                                   
                            l.ledErrore(1,2)                                    
                else:                                                           
                        l.ledErrore(1,3)                                        
    else:                                                                       
        l.ledErrore(1,1)    
                
#FUNZIONAMENTO LED:
#1)tutto bene = led verde
#2)utente ha gia' ritirato il premio = lampeggia 3 volte led rosso
#3)ore non corrette = lampeggia 2 volte led ross
#4)non venerdi', non sono passate le 18 = lampeggia una volta
