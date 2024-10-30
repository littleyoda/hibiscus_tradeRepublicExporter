# licensed under the MIT License
# Sven Bursch-Osewold

import json
import os
from datetime import datetime
from pathlib import Path

from pytr.api import TradeRepublicError
from pytr.utils import  get_logger, preview
from pytr.timeline import Timeline
from requests import session
from requests_futures.sessions import FuturesSession
from yattag import Doc, indent


class HIBISCUS:
    def __init__(
        self,
        tr,
        output_path,
        since_timestamp,
        include_pending,
        save_transcations
    ):
        '''
        tr: api object
        output_path: name of the directory where the downloaded files are saved
        filename_fmt: format string to customize the file names
        since_timestamp: downloaded files since this date (unix timestamp)
        '''
        self.including_pending = include_pending
        history_file='tr2hibiscus.json'
        self.tr = tr
        self.output_path = Path(output_path)
        self.history_file = Path(os.path.join(self.output_path, history_file))
#        self.filename_fmt = filename_fmt
        self.since_timestamp = since_timestamp
        self.save_transcations = save_transcations
 #       self.universal_filepath = universal_filepath

        requests_session = session()
        if tr is not None:
            if self.tr._weblogin:
                requests_session.headers = self.tr._default_headers_web
            else:
                requests_session.headers = self.tr._default_headers
            self.session = FuturesSession(max_workers=1, session=requests_session)
        self.futures = []

        self.docs_request = 0
        self.done = 0
        self.filepaths = []
        self.history = {
            "known_transactions": [] 
        }
        # self.doc_urls = []
        # self.doc_urls_history = []
        self.tl = Timeline(self.tr, self.since_timestamp)
        self.log = get_logger(__name__)
        self.load_history()

    def load_history(self):
        '''
        Read history file with URLs if it exists, otherwise create empty file
        '''
        self.log.info(f"Using {self.history_file}")
        if self.history_file.exists():
            with self.history_file.open() as f:
                self.history = json.load(f) 
        else:
            self.history_file.parent.mkdir(exist_ok=True, parents=True)
          
           # self.history_file.touch()
            #self.log.info('Created history file')

    async def dl_loop(self):

        kontobewegungen = []
        await self.tl.get_next_timeline_transactions()

        while True:
            try:
                _subscription_id, subscription, response = await self.tr.recv()
            except TradeRepublicError as e:
                self.log.fatal(str(e))
            if subscription['type'] == 'timelineTransactions':
                await self.tl.get_next_timeline_transactions(response)
                continue

            if subscription['type'] == 'timelineActivityLog':
                await self.tl.get_next_timeline_activity_log(response)
                continue

            if subscription['type'] != 'timelineDetailV2':
                self.log.warning(f"unmatched subscription of type '{subscription['type']}':\n{preview(response)}")
                continue
            event =  self.tl.timeline_events[response['id']]
            event['details'] = response
            if "amount" in event:
                kontobewegungen.append(event)
                if self.save_transcations:
                    jsonfile = os.path.join(self.output_path, "_" + event["id"])
                    with open(jsonfile, mode='w', encoding='utf-8') as output_file:
                        json.dump(event, output_file)
            self.tl.received_detail += 1
            if self.tl.received_detail == self.tl.requested_detail:
                break

        self.log.error('Received all details')
        self.processKontobewegungen(kontobewegungen)
        exit(0)


    def getSection(self,info, sectionname: list):
        """ Function to extract information from the json data structure """
        try:
            if info is None:
                return None
            if len(sectionname) == 0:
                return info
            if sectionname[0] in info:
                    return self.getSection(info[sectionname[0]], sectionname[1:])
            for i in info:
                # print("1. Info:",info)
                # print("2. Sectionname:",sectionname)
                # print("3. Info2:",i)
                # print("4. ",type(i))
                if isinstance(i, dict) and "title" in i and i["title"] == sectionname[0]:
                    return self.getSection(i, sectionname[1:])
           # self.log.info(f"Section {sectionname} not found")
            return None
        except Exception as e:
            raise e
                  
    def processKontobewegungen(self, kontobewegungen):
        doc, tag, text = Doc().tagtext()

        doc.asis('<?xml version="1.0" encoding="UTF-8"?>')
        # nr = 1
        self.log.info(f"Found {len(kontobewegungen)} Transactions")
        nr = 0
        with tag('objects'):
            for i in kontobewegungen:
                # Check für known transactions
                if i["id"] in self.history["known_transactions"]:
                    self.log.info(f'Already seen {i["id"]}') 
                    continue

                # Check for Pending
                print("ID", i["id"])
                status = self.getSection(i["details"]["sections"],["Übersicht","data","Status","detail", "functionalStyle" ])
                if status not in ["PENDING","EXECUTED","CANCELED"]:
                    self.log.error(f'Unknown status {i["status"]} {status} ID: {i["id"]}')
                    continue
                if status == "CANCELED":
                    continue
                if status == "PENDING" and not self.including_pending:
                    print("Pending")
                    continue
                if status != "PENDING":
                    self.history["known_transactions"].append(i["id"])
                
                # Create Entry
                with tag('object', type="de.willuhn.jameica.hbci.server.UmsatzImpl", id=nr):
                    with tag('datum', type="java.sql.Date"):
                        ts = i["timestamp"]
                        text(f"{ts[8:10]}.{ts[5:7]}.{ts[0:4]} {ts[11:19]}")
                    with tag('valuta',  type="java.sql.Date"):
                        ts = i["timestamp"]
                        text(f"{ts[8:10]}.{ts[5:7]}.{ts[0:4]} {ts[11:19]}")
                    with tag('empfaenger_konto',  type="java.lang.String"):
                        gegenkonto = self.getSection(i["details"]["sections"],["Absender", "data", "IBAN", "detail", "text"])
                        if not gegenkonto:
                            gegenkonto = self.getSection(i["details"]["sections"],["Empfänger", "data", "IBAN", "detail", "text"])
                        if not gegenkonto:
                            gegenkonto = ""
                        text(gegenkonto)
                    with tag('primanota',  type="java.lang.String"):
                        pass
                    with tag('empfaenger_name',  type="java.lang.String"):
                        gegenkonto = self.getSection(i["details"]["sections"],["Absender", "data", "Name", "detail", "text"])
                        if not gegenkonto:
                            gegenkonto = self.getSection(i["details"]["sections"],["Übersicht", "data", "Händler","detail","text"])
                        if not gegenkonto:
                            gegenkonto = self.getSection(i["details"]["sections"],["Empfänger","data","Name","detail","text"])
                        if not gegenkonto:
                            gegenkonto = ""
                        text(gegenkonto)
                    with tag('customerref',  type="java.lang.String"):
                        pass
                        #>2024-07-09-12.16.08.397922</c>
                    with tag('checksum',  type="java.math.BigDecimal"):
                        pass
                        #>1952814358</checksum>
                    with tag('zweck',  type="java.lang.String"):
                        zweck = self.getSection(i["details"]["sections"],["Übersicht", "data", "Referenz","detail","text"])
                        if not zweck:
                            zweck = i["title"]
                        text(zweck)
                    with tag('art',  type="java.lang.String"):
                        text(i["eventType"])
                    with tag('betrag',  type="java.lang.Double"):
                        text(i["amount"]["value"])
                    with tag('konto_id',  type="java.lang.Integer"):
                        pass
                    with tag('addkey',  type="java.lang.String"):
                        pass
                    with tag('txid',  type="java.lang.String"):
                        pass
                    with tag('saldo',  type="java.lang.Double"):
                        pass
                    with tag('gvcode',  type="java.lang.String"):
                        pass
                    with tag('empfaenger_blz',  type="java.lang.String"):
                        pass

                    if status == "PENDING":
                        with tag('flags', type="java.lang.Integer"):
                            text(2)

                    comment = ""
                    if self.getSection(i["details"]["sections"],["Vorteile", "data", "", "detail"]):
                        e = self.getSection(i["details"]["sections"],["Vorteile", "data", "", "detail"])
                        comment += f"{e["title"]} {e["subtitle"]} {e["amount"]}"
                        
                    if self.getSection(i["details"]["sections"],["Transaktion"]):
                        isin = self.getSection(i["details"]["sections"][0],["action"])
                        if (isin is not None and isin.get("type","") == "instrumentDetail"):
                            comment += f"{isin["payload"]}\n"
                        count = self.getSection(i["details"]["sections"],["Transaktion", "data", "Anteile","detail","text"])
                        preis = self.getSection(i["details"]["sections"],["Transaktion", "data", "Anteilspreis","detail","text"])
                        gesamt = self.getSection(i["details"]["sections"],["Transaktion", "data", "Gesamt","detail","text"])
                        gebuehr = self.getSection(i["details"]["sections"],["Transaktion", "data", "Gebühr","detail","text"])
                        comment += f"Anteile: {count}\nPreis pro Anteil: {preis}\nPreis: {gesamt}\nGebühr: {gebuehr}"
                    if comment != "":
                        with tag('kommentar',  type="java.lang.String"):
                            text(comment)


                nr += 1


        result = indent(
            doc.getvalue(),
            indentation = ' '*4,
            newline = '\r\n'
        )

        xmlfile = os.path.join(self.output_path, "hibiscus-"+ datetime.now().isoformat()[0:19].replace(":",".") + ".xml")

        print(f"Transactions to be saved: {nr}")   
        if nr > 0:     
            with open(xmlfile, mode='w', encoding='utf-8') as output_file:
              output_file.write(result)

            with self.history_file.open('w') as history_file:
                json.dump(self.history, history_file)
            print(f"File {xmlfile} ready for import to hibiscus")
