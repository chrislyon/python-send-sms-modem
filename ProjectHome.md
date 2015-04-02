# Description rapide: #
Envoi de SMS via un script python
fonctionne avec un MODEM EGS3.

# Description plus longue #
Au debut il s'agissait d'envoyer des messages, on ouvre le port USB/Serie on envoi les commandes AT et puis c'est tout.

Eh ben non !, cela ne fonctionne que si vous etes tout seul, des que vous voulez envoyer plusieurs SMS cela se complique.

Donc il a fallu rajouter un fichier fifo pour ne pas perdre de SMS a envoyer

Puis il a fallu créer un daemon qui attend que l'on envoi des SMS

Puis il a fallu vérifier que les SMS était bien parti ou on arretait au bout de x essais

Puis il a fallu lire ce fifo de maniere non bloquante pour pouvoir re essayer de renvoyer les SMS qui n'était pas parti.

# Note : #
C'est actuellement en exploitation, dans le cadre de la surveillance de la temperature d'une salle serveur avec envoi de SMS (5 actuellement) si la climatisation tombe en panne