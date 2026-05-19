# Proiect 22 - Tunelare comunicatie printr-un singur port

Implementare proprie de tunel pentru a traversa o zona de retea cu un singur port deschis.

## Arhitectura

Client serviciu -> server tunel local -> server tunel la distanta -> serviciu

Server tunel local:
- asculta pe mai multe porturi configurabile
- pentru fiecare conexiune trimite portul destinatie dorit catre tunelul remote
- apoi face forward bidirectional

Server tunel remote:
- asculta pe un singur port
- citeste portul destinatie din header
- conecteaza local la serviciul corespunzator si face forward

Servicii:
- timp curent (trimite periodic timpul)
- chat/broadcast (relay mesaje text)

## Protocol de incapsulare

La inceputul fiecarei conexiuni:
- clientul tunelului local trimite 2 bytes (uint16 big-endian) cu portul destinatie
- serverul remote raspunde cu status (1 byte) + lungime mesaj (2 bytes) + mesaj
  - 0 = OK
  - 1 = port invalid
  - 2 = serviciu indisponibil

Dupa status OK, se face forward bidirectional al payload-ului.

## Rulare cu Docker (cerinta video)

Pornire:
```
docker compose up --build
```

Client timp prin tunel:
```
python src/clients/time_client.py --host 127.0.0.1 --port 5001
```

Client chat prin tunel (deschide 2 terminale pentru a vedea broadcast):
```
python src/clients/chat_client.py --host 127.0.0.1 --port 5002
```

Demonstratie refuz acces direct (porturile serviciilor nu sunt expuse pe host):
```
python src/clients/time_client.py --host 127.0.0.1 --port 9001
```

Tratare eroare port invalid (mapat 5003 -> 9999):
```
python src/clients/time_client.py --host 127.0.0.1 --port 5003
```

## Rulare fara Docker (optional)

In trei terminale:
```
python src/services/time_server.py --port 9001
python src/services/chat_server.py --port 9002
python src/tunnel_remote.py --listen 7000 --services 9001:127.0.0.1,9002:127.0.0.1
```

In alt terminal:
```
python src/tunnel_local.py --listen 5001:9001,5002:9002,5003:9999 --remote-host 127.0.0.1 --remote-port 7000
```

Clienti:
```
python src/clients/time_client.py --port 5001
python src/clients/chat_client.py --port 5002
```

## Note
- Toate serverele sunt concurente (thread per conexiune)
- Tratare erori: port invalid, serviciu indisponibil, header lipsa
- Nu se folosesc solutii existente de tunelare
