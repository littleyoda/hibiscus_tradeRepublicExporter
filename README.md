# hibiscus_tradeRepublicExporter

Dieses Skript ruft die Transaktion eines Trade Republic Kontos ab und wandelt so in das [Hibiscus](https://www.willuhn.de/products/hibiscus/) Format um. Die Transaktionen können über ["Umsätze Importieren"](https://www.willuhn.de/wiki/doku.php?id=handbuch:umsaetze) importiert werden.
Depotumsätze werden nicht unterstützt.

Das ganze Skript ist ein Proof of Concept. Ich habe nicht die Lust und die Resourcen, um das Skript großartig weiterzuentwickeln. Ich stelle es aber trotzdem zur Verfügung, weil es für mich funktioniert und somit auch für andere nutzlich sein kann.

# Installation
Eine funktionierte Python-Umgebung muss installiert sein.

```
git clone https://github.com/littleyoda/hibiscus_tradeRepublicExporter.git
cd hibiscus_tradeRepublicExporter
python3 -m venv venv
pip install -r requirements.txt
```

# Aufruf
```
cd hibiscus_tradeRepublicExporter

je nach Betriebssystem
. ./venv/bin/activate
venv\Scripts\activate

python3 tr2hibiscusxml.py  hibiscus --last-days 14 hibiscus/
```
Dieser Aufruf ruft die Transaktionen der letzten 14 Tage ab und speichert neue Transaktion als XML-Datei in das Unterverzeichnis hibiscus. Die erstellte XML-Datei kann dann über ["Umsätze Importieren"](https://www.willuhn.de/wiki/doku.php?id=handbuch:umsaetze) importiert werden.

# Bekannte Probleme
* Fondsanteile, die aus dem Cashbank bezahlt werden, erscheinen als "normale" Transaktion. Diese Transaktionen müssen per Hand auf 0 Euro gesetzt werden und in der Kontoübersicht, muss der [Saldo neuberechnet](https://www.willuhn.de/wiki/doku.php?id=support:faq&s[]=salden&s[]=neu&s[]=berechnen#zwischensummen_salden_der_umsaetze_falsch) werden.

