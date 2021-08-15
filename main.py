import os
from datetime import datetime

import credentials
from ts_api import TSDigital


def get_to_send_invoices():
    """
    the function retrieves unsent invoices
    :return:
    """
    sent_invoices_path = "c:\\Users\\SER\\Desktop\\FATTURA PER CLIENTE"
    to_send_invoices_path = "d:\\ItoTech\\Documento\\Fattura_Xml"
    to_send_invoices = {}
    for dir in os.listdir(to_send_invoices_path):
        try:
            to_send_invoices[datetime.strptime(dir, "%Y").year] = []
        except ValueError:
            pass


ts = TSDigital(credentials.email, credentials.password, credentials.VAT_number)
for invoice_path in get_to_send_invoices():
    # print(ts.invoices(invoice_path))
    pass
