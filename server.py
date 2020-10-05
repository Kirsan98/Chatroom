#!/usr/bin/python3
import socket
import select
import sys
 
# Fonction permettant d'envoyer un message à toutes les clients connectés sur le serveur excepté le client envoyant le message et le serveur 
def send_to_all(sock, message):
	for socket in list_connected:
		if socket != serveur_socket and socket != sock:
			try:
				socket.send(message)
			except:
				#  Si la connection n'est pas disponible
				socket.close()
				list_connected.remove(socket)

HOST = ""
PORT = 1459
BUFFER = 4096

# Crée une socket TCP/IP
serveur_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serveur_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# Lier la socket au port
serveur_socket.bind((HOST, PORT))
serveur_socket.listen(5)

list_connected = [] # Liste de tout les clients connectés au serveur
list_connected.append(serveur_socket) 
dico_client = {} # Dictionnaire client contenant ;  # [0] = Adresse du client
                                                    # [1] = nickname
                                                    # [2] = channel du client
                                                    # [3] = bool d'administrateur (True ou False)
                                                    # [4] = (list_channel,list_bool) (example: (["Default","Chan1","Chan2"],[False,True,False]) )
dico_channel = {"Default":[]} # Dictionnaire de channel contenant un channel vide nommé "Défault" lorsque le client se connecte la première fois sur le serveur  
nickname_list = [] # List contenant tout les nick des utilisateurs présents sur le serveur

print("SERVER WORKING !\n")
    
while True:
    rList, _, _ = select.select(list_connected, [], [],0)
    for sock in rList:
        # Nouvelle connection d'un client 
        if sock == serveur_socket:
            sclient, addr = serveur_socket.accept()
            name = sclient.recv(BUFFER).decode()
            dico_channel["Default"].append(sclient) # Ajoute la socket client au channel "Default"
            list_connected.append(sclient)  # Ajoute la socket client à la list des personnes connectés sur le serveur
            print('Connected by', addr)
            dico_client[sclient] = [addr, None, "Default", False,(["Default"],[False])] # Initialise notre dico client 
            while name in nickname_list : # Si le name est déjà utilisé
                sclient.send(b"Username already taken, try another nickname!\n")
                name = sclient.recv(BUFFER).decode()
            dico_client[sclient][1] = name # Administre le name a notre client 
            nickname_list.append(name) # Ajoute name à la list de nickname présent sur le serveur
            send_to_all(sclient,b" ["+ dico_client[sclient][1].encode() + b"] JOIN\n")
        # Nouveau message d'un client
        else:
            try: 
                data1 = sock.recv(BUFFER).decode()
                if not data1:
                    sock.close()
                else:
                    data = data1.split(" ")
                    #KICK <nick> COMMAND (FONCTIONNE)
                    if (data[0] == "/KICK" or data[0]== "/KICK\n"):  
                        if (len(data)<2):
                            sock.send(b"Nick name not indicated\n")
                        elif (len(data)==2):
                            if dico_client[sock][3] != True :
                                sock.send(b"You don't have the permission\n")
                            elif not data[1][:-1] in nickname_list:
                                sock.send(b"Invalid nick name\n")
                            else : 
                                if dico_client[sock][2] == "Default" : 
                                    sock.send(b"You can not kick a user which is not currently in a channel\n")
                                else :
                                    for socket in dico_channel[dico_client[sock][2]]: # Je parcours les sockets présente dans le channel courant
                                        if dico_client[socket][1] == data[1][:-1]: # Si le nickname de la socket est identique au <nick>
                                            if (len(dico_client[socket][4][0])>2): # Si la longueur de la liste de channel du client est supérieur à 2 (ex:["Default","chan1","chan2"] )
                                                dico_channel[dico_client[socket][2]].remove(socket) # on remove la socket du channel
                                                cpt = dico_client[socket][4][0].index(dico_client[socket][2]) #  V1 : on récupère l'index du channel dans la liste_canal du client
                                                dico_client[socket][4][0].remove(dico_client[socket][2]) # on supprime le channel de la liste channel du client kicked
                                                dico_client[socket][4][1].remove(dico_client[socket][4][1][cpt]) # on supprime le booleen indiquant [admin] de la list de bool du client
                                                dico_client[socket][2] = dico_client[socket][4][0][1] # on fixe le champ channel actuel du client au premier channel rejoint après "Default"
                                                sock.send(b"User " + data[1][:-1].encode() + b" has been kick from the current channel\n")
                                                socket.send(b"You have been kicked from the channel\n")
                                            elif (len(dico_client[socket][4][0])==2): # Si la longueur de la liste de channel du client est égale à 2 (ex:["Default","Chan1_to_leave"])
                                                dico_channel[dico_client[socket][2]].remove(socket) # On remove la socket du channel quitté
                                                socket.send(b"You have left channel " + dico_client[socket][2].encode() + b"! You are back in Default channel!\n")
                                                dico_client[socket][4][0].remove(dico_client[socket][2]) # On supprime le channel de la liste channel du client kicked
                                                dico_client[socket][4][1].remove(dico_client[socket][4][1][1]) # On supprime le booleen indiquant [admin] de la list de bool du client
                                                dico_client[socket][2] = "Default" # Initialise le channel courant du client
                                                dico_client[socket][3] = False # Initialise les droits d'admin du client
                                                sock.send(b"User " + data[1][:-1].encode() + b" has been kick from the current channel\n")
                                                socket.send(b"You have been kicked from the channel\n")
                                        else :
                                            continue
                        else:
                            sock.send(b"Invalid argument given\n")
                    #JOIN <channel> COMMAND (FONCTIONNE)
                    if data[0] == "/JOIN" or data[0] == "/JOIN\n" :
                        if (len(data) < 2):
                            sock.send(b"Channel name not indicated!\n")
                        elif(len(data) == 2):
                            if data[1][:-1] in dico_client[sock][4][0] or data[1][:-1]==dico_client[sock][2]: # Si le nom du channel est égale au channel actuel ou si le channel appartient a notre list channel du client
                                sock.send(b"You can't join a channel you already joined!\n")
                            elif data[1][:-1] in dico_channel.keys(): # On rejoins un channel existant
                                dico_client[sock][2] = data[1][:-1] #Channel --> "Channel_name"
                                dico_client[sock][3] = False # Initialise [admin] du client
                                dico_client[sock][4][0].append(data[1][:-1]) # Ajoute le channel a la list_channel du client
                                dico_client[sock][4][1].append(False) # Ajoute le bool à la list_bool du client
                                dico_channel[data[1][:-1]].append(sock) #Ajout socket_c à la liste du channel
                                sock.send(b"You have joined " + data[1][:-1].encode() + b" !\n")
                            else: #On crée un nouveau channel
                                dico_channel[data[1][:-1]] = [sock] #on créer le couple key:value (nom channel : socket_participants)
                                sock.send(b"Channel --> "+ data[1].encode() + b" has been created!\n")
                                dico_client[sock][2] = data[1][:-1] # modification channel sock
                                dico_client[sock][3] = True #le premier a créer devient admin
                                dico_client[sock][4][0].append(data[1][:-1]) # Ajoute le channel a la liste du channel du client
                                dico_client[sock][4][1].append(True) # Ajoute le bool à la list_bool du client
                                sock.send(b"You have joined " + data[1][:-1].encode() + b" as admin!\n")
                        else: 
                            sock.send(b"Invalid argument given\n")
                    # CURRENT <channel> COMMAND
                    elif data[0]=="/CURRENT" or data[0]=="/CURRENT\n":
                        if (len(data) < 2):
                            sock.send(b"Current channel is --> "+dico_client[sock][2].encode()+b" !\n") # CURRENT COMMAND (print current channel)
                        elif (len(data)==2):
                            if not data[1][:-1] in dico_client[sock][4][0]: # Si le <channel> n'appartient pas à dico_client[sock][4]
                                sock.send(b"You are not in the channel, join it before doing this command\n")
                            elif dico_client[sock][2] == data[1][:-1]: # Si le <channel> est déjà le channel_courant
                                sock.send(b"The <channel> is already your current channel\n")
                            else: 
                                dico_client[sock][2] = data[1][:-1] # Le channel courant deviens <channel>
                                cpt = dico_client[sock][4][0].index(data[1][:-1]) # Récupère l'index dans la liste_channel du client le channel <channel>
                                dico_client[sock][3] = dico_client[sock][4][1][cpt] # Administre le booléen [admin] équivalent à son channel
                                sock.send(b"Your current channel is now "+ data[1][:-1].encode()+b" !\n")
                        else: 
                            sock.send(b"Invalid argument given\n")
                    #WHO COMMAND (FONCTIONNE)
                    elif data[0] == "/WHO" or data[0] == "/WHO\n":
                        sock.send(b"List of channel participants: \n")
                        for i in dico_channel[dico_client[sock][2]]: # Parcours la liste des personnes dans le channel courant
                            if dico_client[i][2] == dico_client[sock][2]:
                                if dico_client[i][3]==True: # Si l'utilisateur est un admin : - @nick@
                                    sock.send(b" - " +b"@"+dico_client[i][1].encode()+b"@"+ b"\n")
                                else: # Si l'utilisateur n'est pas un admin : - nick
                                    sock.send(b" - " + dico_client[i][1].encode()+ b"\n")
                            else:
                                if dico_client[sock][2] in dico_client[i][4][0]:
                                    indexe = dico_client[i][4][0].index(dico_client[sock][2])
                                    if dico_client[i][4][1][indexe] == True:
                                        sock.send(b" - " +b"@"+dico_client[i][1].encode()+b"@"+ b"\n")
                                    else:
                                        sock.send(b" - "+ dico_client[i][1].encode() + b"\n")
                    #LIST COMMAND (FONCTIONNE)
                    elif data[0] == "/LIST" or data[0] == "/LIST\n":
                        sock.send(b"List of all available channels on the chatroom:\n")
                        for i in list(dico_channel): # Parcours la liste des channels existant sur le serveur
                            sock.send(b" - " + i.encode() + b"\n")
                    #BYE COMMAND (FONCTIONNE)
                    elif data[0] == "/BYE" or data[0] == "/BYE\n":
                        if dico_client[sock][2]!="Default": # Ne peut pas utiliser cette commande si je ne suis pas dans un channel
                            sock.send(b"Leave current channel before using BYE\n")
                        else : 
                            sock.sendall(b"Client "+ dico_client[sock][1].encode() + b" is offline!\n")
                            dico_channel[dico_client[sock][2]].remove(sock) # Supprime la socket client du channel 'Default'
                            nickname_list.remove(dico_client[sock][1]) # Supprime le nick client de la liste de nick_name présent sur le serveur
                            list_connected.remove(sock) # Supprime la socket client de notre liste de client connecté au serveur
                            del dico_client[sock] # Supprime le dico_client correspondant a la socket
                            sock.close() # Ferme la socket
                            continue
                    #HELP COMMAND (FONCTIONNE)
                    elif data[0] == "/HELP" or data[0] == "/HELP\n": # Envoie la liste des commande valables 
                        sock.send(b"\nCommand enable for users:\n/LIST: list all available channels on server\n/JOIN <channel>: join (or create) a channel\n/LEAVE: leave current channel\n/WHO: list users in current channel\n<message>: send a message in current channel\n/MSG <nick> <message>: send a private message in current channel\n/BYE: disconnect from server\n/KICK <nick>: kick user from current channel [admin]\n/REN <channel>: change the current channel name [admin]\n")
                    #LEAVE COMMAND
                    elif data[0] == "/LEAVE" or data[0] == "/LEAVE\n":
                        if (len(data)==1):
                            if dico_client[sock][2]=="Default": # Ne peut pas quitter le channel Default
                                sock.send(b"Can't leave default channel!\n")
                            if dico_client[sock][2]!="Default":
                                if len(dico_channel[dico_client[sock][2]])>=2 and dico_client[sock][3] == True : # Si l'admin veut quitter le channel et qu'il a plus de 1 personne dans le channel.
                                    dico_client[dico_channel[dico_client[sock][2]][1]][3] = True # On attribue l'admin à la deuxième personne ayant rejoint le serveur.
                                if (len(dico_client[sock][4][0])>2): # Si la longueur de la list de channel du client est supérieur à 2 (ex:["Default","chan1","chan2"] )
                                    dico_channel[dico_client[sock][2]].remove(sock) # On remove la socket du channel
                                    if dico_channel[dico_client[sock][2]]==[]: # Si il n'y a plus personne dans le channel alors on le supprime
                                        del dico_channel[dico_client[sock][2]]
                                    cpt = dico_client[sock][4][0].index(dico_client[sock][2]) #  V1 : On récupère l'index du channel dans la liste_canal du client
                                    dico_client[sock][4][0].remove(dico_client[sock][2]) # On supprime le channel quitté de la liste channel
                                    dico_client[sock][4][1].remove(dico_client[sock][4][1][cpt]) # On supprime le booleen correspondant à l'index du client
                                    dico_client[sock][2] = dico_client[sock][4][0][1] # On fixe le champ channel actuel du client au premier channel rejoint après "Default"
                                    sock.send(b"You are now back in " + dico_client[sock][2].encode() + b" !\n")
                                elif (len(dico_client[sock][4][0])==2): # Si la longueur de la liste de channel du client est égale à 2
                                    dico_channel[dico_client[sock][2]].remove(sock) # On remove la socket du channel quitté
                                    if dico_channel[dico_client[sock][2]]==[]: # Si il n'y a plus personne dans le channel alors on le supprime
                                        del dico_channel[dico_client[sock][2]]
                                    sock.send(b"You have left channel " + dico_client[sock][2].encode() + b"! You are back in Default channel!\n")
                                    dico_client[sock][4][0].remove(dico_client[sock][2]) # Supprime le channel de la list de channel du client
                                    dico_client[sock][4][1].remove(dico_client[sock][4][1][1]) # Supprime le booléen correspondant au channel quitté
                                    dico_client[sock][2] = "Default" # Initialise le channel courant du client
                                    dico_client[sock][3] = False # Initialise les droits d'admin du clients
                    #MSG <nick> <msg> COMMAND (FONCTIONNE)
                    elif data[0] == "/MSG" or data[0] == "/MSG\n":
                        if (len(data) < 3):
                            sock.send(b"Nick or message not indicated\n")
                        elif not data[1] in nickname_list: # Si le nick n'appartient a aucun nick_name sur le serveur
                            sock.send(b"User: "+ data[1].encode() + b" is not in your current channel!\n")
                        else :
                            for socket in dico_channel[dico_client[sock][2]]: # Je parcours les sockets présente dans le même channel que le client
                                if dico_client[socket][1] == data[1]: # Si le nom entré est identique au nom du client ayant la socket i
                                    socket.send(dico_client[sock][1].encode() + b" send you as private message: ")
                                    for i in range (len(data)):
                                        if i>=2:
                                            socket.send(data[i].encode()+b" ") # Je lui envoie le message
                                        else :
                                            continue
                                else :
                                    continue
                    #GRANT <nick> COMMAND && REVOKE <nick> COMMAND (EXTENSION) (FONCTIONNE) (V1)
                    elif data[0]=="/GRANT" or data[0]=="/GRANT\n" or data[0]=="/REVOKE" or data[0]=="/REVOKE\n":
                        if (len(data) < 2):
                            sock.send(b"Nickname to grant not indicated\n")
                        elif (len(data) == 2 ):
                            if dico_client[sock][3]!=True: # Si le client utilisant la commande n'est pas un admin
                                sock.send(b"You dont have permission for this command\n")
                            elif not data[1][:-1] in nickname_list: # Si le <nick> n'appartient pas à la liste de nickname
                                sock.send(b"Invalid nickname indicated or <nick> is not in your current channel\n")
                            else:
                                for socket in dico_channel[dico_client[sock][2]]: # Je parcours la liste des sockets présente dans le channel courant
                                    if dico_client[socket][1]==data[1][:-1]: # Si le nick de la socket est identique au <nick>
                                        if data[0]=="/GRANT" or data[0]=="/GRANT\n":
                                            if dico_client[socket][2] == dico_client[sock][2]: # si le dico_client parcouru à son champ channel courant égale au channel courant de celui qui a tapé la commande
                                                dico_client[socket][3]=True # Administre les droits d'admin au <nick>
                                                socket.send(b"You are now consider as an admin in the current channel\n")
                                                sock.send(b"You granted "+ data[1][:-1].encode() + b" as an admin\n")
                                            else:
                                                if dico_client[sock][2] in dico_client[socket][4][0]: # si le channel actuel de celui qui tape la commande est dans la liste des channels des dico_client parcouru
                                                    indexe = dico_client[socket][4][0].index(dico_client[sock][2])
                                                    dico_client[socket][4][1][indexe] = True
                                                    sock.send(b"You granted "+ data[1][:-1].encode() + b" as an admin\n")
                                                    socket.send(b"You are now consider as an admin in " + dico_client[sock][2].encode() + b" channel\n")
                                        elif data[0]=="/REVOKE" or data[0]=="/REVOKE\n":
                                            if dico_client[socket][2] == dico_client[sock][2]: # si le dico_client parcouru à son champ channel courant égale au channel courant de celui qui a tapé la commande
                                                dico_client[socket][3]=False # Administre les droits d'admin au <nick>
                                                socket.send(b"You are not anymore consider as an admin in the current channel\n")
                                                sock.send(b"You revoked "+ data[1][:-1].encode() + b" as a client\n")
                                            else:
                                                if dico_client[sock][2] in dico_client[socket][4][0]: # si le channel actuel de celui qui tape la commande est dans la liste des channels des dico_client parcouru
                                                    indexe = dico_client[socket][4][0].index(dico_client[sock][2])
                                                    dico_client[socket][4][1][indexe] = False
                                                    socket.send(b"You are not anymore consider as an admin in" + dico_client[sock][2].encode() + b" channel\n")
                                                    sock.send(b"You revoked "+ data[1][:-1].encode() + b" as a client\n")


                                    else :
                                        continue
                        else: 
                            sock.send(b"Invalid argument given\n")
                    #NICK <nick> COMMAND
                    elif data[0] == "/NICK" or data[0]=="/NICK\n": 
                        if (len(data) < 2):
                            sock.send(b"New nick name not indicated !\n")
                        elif (len(data)==2):
                            if data[1][:-1]==dico_client[sock][1]: # Si <nick> est identique à celui de l'utilisateur
                                sock.send(b"You already have this nickname\n")
                            elif data[1][:-1] in nickname_list: # Si <nick> est déjà dans la liste de nick-name
                                sock.send(b"Nick name already used , try "+data[1][:-1].encode()+b"1"+b"\n")
                            elif not data[1][:-1] in nickname_list: # Si le <nick> n'existe pas dans la liste de nick présent sur le serveur
                                nickname_list.remove(dico_client[sock][1]) # Supprime le nick du client de la liste de nick 
                                dico_client[sock][1] = data[1][:-1] # Modifie le nick du client
                                nickname_list.append(data[1][:-1]) # Ajoute le nick du client à la list de nick
                                sock.send(b"You are now known as "+data[1][:-1].encode()+b"\n")
                        else: 
                            sock.send(b"Invalid argument given\n")
                    #REN <channel> COMMAND (FONCTIONNE)
                    elif data[0] == "/REN" or data[0] == "/REN\n":
                        if (len(data) < 2):
                            sock.send(b"New channel name not indicated !\n")
                        elif (len(data) == 2 ):
                            if dico_client[sock][3] != True:
                                sock.send(b"You don't have the permission\n")
                            else:
                                dico_channel[data[1][:-1]] = dico_channel[dico_client[sock][2]] # Crée une nouvelle clé dans le dico_channel {nom modifié : liste des sockets présentes dans le channel à rename}
                                tmp = dico_client[sock][2] # Je stock le nom du channel avant renommage
                                for socket in dico_channel[tmp]: # Je parcours les sockets présente dans le même channel que le client
                                    if dico_client[socket][2] != tmp :
                                        for old_to_change in dico_client[socket][4][0]:
                                            if old_to_change == tmp:
                                                indexe = dico_client[socket][4][0].index(old_to_change)
                                                dico_client[socket][4][0][indexe] = data[1][:-1]
                                    else:
                                        dico_client[socket][2] = data[1][:-1]
                                # Ici toutes les sockets présentent dans le même channel que le client(admin) compris, on le champ channel au nouveau nom voulu
                                del dico_channel[tmp] # Je supprime la paire (key)Nom ancien channel : (value)liste de sockets présentent dedans
                                sock.sendall(b"Channel has been renamed as : " + data[1][:-1].encode() + b" !\n")
                        else: 
                            sock.send(b"Invalid argument given\n")
                    #SEND A MESSAGE TO EVERYONE IN CURRENT CHANNEL
                    else : 
                        msg = " ".join(data) # Permet de regrouper le tableau de mots en une chaine de caractères.
                        for socket in dico_channel[dico_client[sock][2]]: # Parcourt la liste des sockets présentent dans le channel
                            if dico_client[socket][2] == dico_client[sock][2]: # Envoie un message à tous ceux ayant le même channel courant que le client
                                if socket != sock and socket != serveur_socket: # Si la socket est != de l'expéditeur et du serveur
                                    socket.send(dico_client[sock][1].encode()+b": "+ msg.encode())  # On envoie le message à socket
                            else: 
                                continue
            except: # Lorsque le client se déconnecte brutalement du serveur
                list_connected.remove(sock) # Supprime le client de la list_connected
                sys.stdout.write("\n[*] (%s:%s) logged out.\n" % addr)
                del dico_client[sock] # Supprime le dico du client
                sock.close() # Ferme la socket du client 
serveur_socket.close()