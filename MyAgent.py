#!/usr/bin/env python
# -*- coding: utf-8 -*-import spade
"""
SMA's curso 2014-2015
Sistema Multi Agente para obtener las noticias más populares en twitter
"""
__author__ = 'Basilio Carrero Nevado & Daniel Jiménez Rodríguez'

import pickle
import spade
import os
import tweepy
from tweepy import Stream
from tweepy.streaming import StreamListener
from twill.commands import *
from Tkinter import *
from ttk import Treeview, Label
from BeautifulSoup import BeautifulSoup
from PIL import ImageTk, Image
import webbrowser


dic = {}
filename = 'dataObject'
# Receiver Agent
name = 'titler'
ip = '127.0.0.1'
# Access keys & tokens
consumer_key = '3Tw1LEZak7XW3rtpEyS0yU1ll'
consumer_secret = '6ovPKYdPLEqmQ2GHyj7UvCxN5MoM8kuGqjc04TO0A70p3MlyIp'
access_key = '487491439-pFZder2DpC4cp30ZNBzQBvmE28gC0Xm4dAeNj4kU'
access_secret = '1gzqgkq0kZxaLpBjRVbbe5cHqa11bqJ6LHjBHqZpsHbNe'
# Terms to track
trackTags = [u'España', u'noticias', u'europa', u'deportes', u'economía',
             u'política', u'sociedad', u'música', u'cultura', u'nacional', u'internacional']
# Trusted sources
fuentes = [u'.elmundo.es', u'.20minutos.es', u'.abc.es', u'.eldiario.es', u'.elpais.com',
           u'.eleconomista.es', u'.as.com', u'.marca.com', u'.mundodeportivo.com', u'.antena3.com',
           u'.lainformacion.com', u'.publico.es', u'.ultimahora.es', u'.lavanguardia.com', u'.sport.es']


class Sender(spade.Agent.Agent):

    def __init__(self, agentjid, password):
        super(Sender, self).__init__(agentjid, password)
        self.stream = None
        self.receiver = spade.AID.aid(name='%s@%s' % (name, ip), addresses=['xmpp://%s@%s' % (name, ip)])

    class TwitterBehav(spade.Behaviour.OneShotBehaviour):

        def _process(self):
            self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            self.auth.set_access_token(access_key, access_secret)
            self.myAgent.stream = Stream(self.auth, Sender.StdOutListener(self.myAgent))
            self.myAgent.stream.filter(track=trackTags, languages=['es'], async=True)

    class StdOutListener(StreamListener):

        def __init__(self, ag):
            super(Sender.StdOutListener, self).__init__()
            self.agent = ag

        def on_error(self, status):
            print 'Error:', status

        def on_status(self, status):
            if len(status.entities['urls']) > 0:
                for link in status.entities['urls']:
                    u = link['expanded_url']
                    if any(f in u for f in fuentes):
                        self.agent.sendmsg(u)
                    else:
                        print 'Tweet descartado'

    def sendmsg(self, content):
        _msg = spade.ACLMessage.ACLMessage()  # Instantiate the message
        _msg.setPerformative("inform")        # Set the "inform" FIPA performative
        _msg.setOntology("myOntology")        # Set the ontology of the message content
        _msg.setLanguage("OWL-S")	          # Set the language of the message content
        _msg.addReceiver(self.receiver)       # Add the message receiver
        _msg.setContent(content)              # Set the message content
        self.send(_msg)

    def takeDown(self):
        self.stream.disconnect()

    def _setup(self):
        print "Iniciando capturador de enlaces . . ."
        self.twb = Sender.TwitterBehav()
        self.setDefaultBehaviour(self.twb)


class Receiver(spade.Agent.Agent):

    class Titler(spade.Behaviour.Behaviour):

        def _process(self):
            self.msge = self._receive(True)
            # Se toma el contenido del mensaje (la url)
            self.pagina = self.msge.getContent()
 
            # Check wether the message arrived
            if self.pagina.startswith("http"):

                if self.pagina not in dic.keys():
                    # Se dirige al enlace que le pasan
                    go(self.pagina)
                    # Se guarda el html al fichero
                    save_html('file')
                    f = open('file', 'r')
                    soup = BeautifulSoup(f.read())
                    f.close()
                    os.remove('file')
                    # Se parsea el título de la noticia
                    titulo = soup.find('title')
                    text = titulo.text
                    dic[self.pagina] = (text, 1)
                    print u'Nuevo Título: %s' % text

                else:
                    # Incrementar para esa url el contador de repeticiones
                    (titulo, repeticiones) = dic[self.pagina]
                    dic[self.pagina] = (titulo, repeticiones + 1)
                    print u'%d Repeticiones, Título: %s' % (repeticiones + 1, titulo)

    def takeDown(self):
        self.removeBehaviour(self.rb)
        try:
            with open(filename, 'wb') as handle:
                pickle.dump(dic, handle)
        except IOError:
            print 'No se puede escribir el fichero'

    def _setup(self):
        global dic
        print "Iniciando manejador de enlaces . . ."
        try:
            with open(filename, 'rb') as handle:
                dic = pickle.load(handle)
        except IOError:
            print 'No se puede leer el fichero'
            dic = {}
        self.rb = Receiver.Titler()
        self.setDefaultBehaviour(self.rb)


class MainWindow(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.treeview = None
        self.createui()
        self.loadtable()
        self.grid(sticky=(N, S, W, E))
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

    def createui(self):
        image = Image.open('header.png')
        photo = ImageTk.PhotoImage(image)
        lbl = Label(self, image=photo)
        lbl.image = photo
        lbl.grid(row=0, column=0, columnspan=2, sticky='ns')
        self.treeview = Treeview(self)
        self.treeview['columns'] = ['title']
        self.treeview.heading("#0", text='Repeticiones', anchor='center')
        self.treeview.column("#0", anchor="center", width=90)
        self.treeview.heading('title', text='Titulo', anchor='w')
        self.treeview.column('title', anchor='w', width=700)
        self.treeview.grid(sticky=(N, S, W, E))
        self.treeview.bind("<Double-1>", self.openlink)
        ysb = Scrollbar(self, width=18, orient='vertical', command=self.treeview.yview)
        ysb.grid(row=1, column=1, sticky='ns')
        self.treeview.configure(yscroll=ysb.set)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def openlink(self, event):
        item = self.treeview.identify('item', event.x, event.y)
        web = self.treeview.item(item, 'values')[1]
        webbrowser.open_new(web)

    def loadtable(self):
        self.treeview.delete(*self.treeview.get_children())
        sorted_x = sorted(dic.items(), key=lambda x: x[1][1], reverse=True)
        for key, value in sorted_x:
            self.treeview.insert('', 'end', text=str(value[1]), values=[value[0], key])


def refresher(frame):
    frame.loadtable()
    frame.after(1000, refresher, frame)


def setui():
    root = Tk()
    root.wm_title("Tweets Populares:")
    root.resizable(width=FALSE, height=FALSE)
    root.geometry("%dx%d+0+0" % (1000, 650))
    gui = MainWindow(root)
    refresher(gui)
    root.mainloop()


if __name__ == "__main__":
    print __doc__, __author__
    Sender("reader@127.0.0.1", "secret").start()
    Receiver("titler@127.0.0.1", "secret").start()
    setui()
