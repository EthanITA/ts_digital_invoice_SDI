import os
import shutil
from datetime import datetime
from typing import Iterable

from rich import print

import credentials
from log import logging
from ts_api import TSDigital


class Invoice:
    def __init__(self, base_path):
        """
        The given path has to be the following tree structure (as ITO's one):
                        base_path
                    /       /   \
                2021    2022    ....
                /   \
            2021-02 ...
            /   \
        ...xml  ...xml

        - The max and min depth of the tree is always 4  (if has any invoices)
        - The width of the tree is variable based on the depth:
            - 1. the size has virtually no upperbound, and it represents the year of the invoices
            - 2. the size is at most 12 (months), and it represents the month of the invoices
            - 3. the size is equal how many invoices are generated in a given month
        - the nodes and leaves has to follow a certain naming based on the depth, otherwise they will be ignored:
            - 1. year 'YYYY'
            - 2. month 'YYYY-MM'
            - 3. xml files '*.xml'
        :param base_path:
        """
        self.invoices_path = self.get_invoices_path(base_path)

    @staticmethod
    def get_invoices_path(path: str):
        def is_year(year):
            try:
                if datetime.strptime(year, "%Y").year == datetime.today().year:
                    return True
                return False
            except ValueError:
                return False

        def is_year_month(year_month):
            try:
                datetime.strptime(year_month, "%Y-%m")
                return True
            except ValueError:
                return False

        invoices_path = []
        for dirpath, dirnames, filenames in os.walk(path):
            parent_path, actual_dir = os.path.split(dirpath)
            parent_dir = os.path.split(parent_path)[1]
            if is_year(parent_dir) and is_year_month(actual_dir):
                invoices_path += [(dirpath, invoice) for invoice in filenames if invoice[-4:] == ".xml"]
        return invoices_path

    @property
    def basenames(self) -> Iterable[str]:
        """
        the function gets basenames
        :return:
        """
        return list(map(lambda path: path[1], self.invoices_path))

    def basename(self, path: str) -> str:
        return os.path.basename(path)

    def to_full_path(self, name: str) -> str:
        for dirpath, filename in self.invoices_path:
            if filename == name:
                return os.path.join(dirpath, filename)


def get_unsent_invoices() -> list:
    """
    the function retrieves sorted unsent invoices
    :return:
    """
    import json

    i_invoices = set(ito_invoices.basenames)
    s_invoices = set(sent_invoices.basenames)
    unsent_invoices = sorted(i_invoices.difference(s_invoices))
    logging.info(f"unsent={json.dumps(unsent_invoices, indent=4, sort_keys=True)}")
    return [ito_invoices.to_full_path(filename) for filename in unsent_invoices]


def send_invoices(path):
    ts = TSDigital(credentials.email, credentials.password, credentials.VAT_number)
    sent = 0
    for invoice_path in path:
        base_info = ts.invoices(invoice_path)
        if base_info is not None:
            sent += 1
            destination_path = invoice_path.replace(to_send_invoices_path, sent_invoices_path)

            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            shutil.copyfile(invoice_path, destination_path)

            print()
            print(f"[bold green][i]{os.path.basename(destination_path)}[/i][/bold green]")
            print(
                f"\t{base_info['senderName']} ==[bold cyan][{base_info['invoiceNumber']}][{base_info['date']}][/bold cyan]==> [u]"
                f"{base_info['recipientName']} ({base_info['recipientId']})[/u]")
    return sent


sent_invoices_path = "c:\\Users\\SER\\Desktop\\FATTURA PER CLIENTE"
to_send_invoices_path = "d:\\ItoTech\\Documento\\Fattura_Xml"

sent_invoices = Invoice(sent_invoices_path)
ito_invoices = Invoice(to_send_invoices_path)

to_send_invoices = get_unsent_invoices()
if len(to_send_invoices) > 0:

    print(f"\n  Fatture Inviate: {send_invoices(to_send_invoices)}/{len(to_send_invoices)}")
else:
    print("[bold red]Nessuna fattura da inviare[/bold red]")
input("\nPremere invio per continuare...")
