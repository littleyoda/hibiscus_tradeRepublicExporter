# hibiscus_tradeRepublicExporter

Dieses Skript ruft die Transaktion eines Trade Republic Kontos ab und wandelt so in das [Hibiscus](https://www.willuhn.de/products/hibiscus/) Format um. Die Transaktionen können über ["Umsätze Importieren"](https://www.willuhn.de/wiki/doku.php?id=handbuch:umsaetze) importiert werden.
Depotumsätze werden nicht unterstützt.

Das ganze Skript ist ein Proof of Concept. Ich habe nicht die Lust und die Resourcen, um das Skript großartig weiterzuentwickeln.

Ich stelle es aber trotzdem zur Verfügung, weil es für mich funktioniert.

# Installation
Eine funktionierte Python-Umgebung muss installiert sein.

```
git clone https://github.com/littleyoda/hibiscus_tradeRepublicExporter.git
cd hibiscus_tradeRepublicExporter
python3 -v venv venv
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

