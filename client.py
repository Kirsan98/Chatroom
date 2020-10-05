#!/usr/bin/python3
import socket
import select
import sys
import string

HOST = "localhost"
PORT = 1459

# Demande de créer un user name
name = input("CREATING NEW ID:\n" + "Enter username:")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1)

# Se connecte à l'host
try:
    s.connect((HOST, PORT))
except:
    print(b"Can't connect to the server\n")
    sys.exit()

# Si le client est connecté
s.send(bytes(name, "utf-8"))
while 1:
    socket_list = [sys.stdin, s]
    # Obtiens la liste des sockets lisables
    try:
        rList, _, _ = select.select(socket_list, [], [],0)
    except:
        pass
    for sock in rList:
        # Si un message arrivant du serveur
        if sock == s:
            data = sock.recv(4096)
            if not data: # Si le message venant du serveur est invalid
                print("DISCONNECTED!!\n")
                socket_list.remove(sock)
                sys.exit()
            else:
                sys.stdout.write(data.decode())
                sys.stdout.flush()
        # Si un utilisateur entre un message
        else:
            msg = sys.stdin.readline()
            if not msg : # On arrive pas à lire le message alors on ferme la socket et ferme le client
                socket_list.remove(sock)
                sock.close()
                sys.exit()
            else:
                s.send(msg.encode()) # On envoie le message entré au serveur
                sys.stdout.flush()