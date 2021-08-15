import json
import uuid
from hashlib import sha256
from typing import TextIO, Union, Iterable

import requests

from log import logging


class TSDigital:
    flow_type = "SDI"

    def __init__(self, email: str, password: str, VAT_number: str):
        """

        :param email: login email
        :param password: plain text of the password, it will only be used to get the digest
        :param VAT_number: company's VAT number (Partita I.V.A.)
        """
        self.email = email
        self.digest = self.get_digest(password)
        self.VAT_number = VAT_number
        self.bearer_token = self.login()

    def get_digest(self, password):
        """
        the function compute the digest needed to login
        :param password:
        :return:
        """
        sha256_email_password = sha256(f'{self.email}{password}'.encode('utf-8')).hexdigest()
        return sha256(f"{sha256_email_password}{self._get_nonce()}".encode('utf-8')).hexdigest()

    def _get_nonce(self) -> str:
        """
        get a nonce that will be used to create the digest
        :return:
        """
        headers = {
            'x-correlation-id': str(uuid.uuid4()),
            'x-app-version': '1.0',
            'x-app-name': 'PORTALE',
        }

        response = requests.get(f'https://ts-portale-api.agyo.io/login/agyo/nonce?userId={self.email}',
                                headers=headers)
        status_code = response.status_code
        if status_code == 200:
            return response.json()["nonce"]
        else:
            logging.error(f"Status code={status_code}\tmsg={response.text}")

    def login(self) -> str:
        """
        API: https://ts-portale-api.agyo.io/login/agyo
        Get the Bearer token from TS Digital
        :return: 
        """

        headers = {
            'x-correlation-id': str(uuid.uuid4()),
            'x-app-version': '1.0',
            'content-type': 'application/json',
            'x-app-name': 'PORTALE',
        }

        data = json.dumps({
            "id": self.email,
            "digest": self.digest
        })

        response = requests.post('https://ts-portale-api.agyo.io/login/agyo', headers=headers, data=data)
        status_code = response.status_code
        if status_code == 200:
            token = response.json()["token"]
            logging.info(f"bearer token={token}")
            return f"Bearer {token}"
        else:
            logging.error(f"Status code={status_code}\tmsg={response.text}")

    @staticmethod
    def base64encode(f: TextIO) -> str:
        """
        The function encode a TextIO (or with open(..) as f) in base64
        :param f:
        :return:
        """
        from base64 import b64encode
        return b64encode(bytes(f.read(), encoding="utf-8")).decode("utf-8")

    def _build_invoices(self, paths: Iterable[str]) -> list[dict]:
        """
        this function create the data structure needed for extractBaseInfo "invoices" API
        :param paths: list xml paths
        :return:
        """
        assert any([path[-4:] == ".xml" for path in paths])
        import os
        invoices = []
        for i, path in enumerate(paths):
            with open(path) as f:
                invoices.append({
                    "id": f"{os.path.basename(f.name)}{i}",
                    "content": self.base64encode(f),
                    "type": "text/xml",
                    "name": f.name
                })
        return invoices

    def extract_base_info(self, *paths: str) -> Union[list[dict], None]:
        """
        API: https://ts-console-api.agyo.io/xmlInvoices/extractBaseInfo
        The API gives base infos from xmls
        :param paths:
        :return:
        """
        headers = {
            'authorization': self.bearer_token,
            'content-type': 'application/json;charset=UTF-8',
        }

        data = json.dumps({
            "invoices": self._build_invoices(paths),
            "transmitterId": self.VAT_number,
            "flowType": self.flow_type
        })

        response = requests.post('https://ts-console-api.agyo.io/xmlInvoices/extractBaseInfo', headers=headers,
                                 data=data)
        if response.status_code == 200:
            return [res for res in response.json() if not res["errorExtractingData"]]
        else:
            logging.error(f"Status code={response.status_code}\tmsg={response.text}")

    def invoices(self, path: str):
        """
        API: https://ts-console-api.agyo.io/invoices
        This API sends an invoice to the SDI
        :param path:
        :return:
        """
        headers = {
            'authorization': self.bearer_token,
            'content-type': 'application/json;charset=UTF-8',
        }
        base_info = self.extract_base_info(path)[0]
        with open(path) as f:
            data = json.dumps({
                "content": self.base64encode(f),
                "transmitterId": self.VAT_number,
                "senderId": self.VAT_number,
                "recipientId": base_info["recipientId"],
                "name": base_info["id"][:-1],
                "flowType": self.flow_type,
                "transmissionFormat": base_info["transmissionFormat"]}
            )

        response = requests.post('https://ts-console-api.agyo.io/invoices', headers=headers, data=data)

        if response.status_code == 201:
            logging.info(
                f"{base_info['senderName']} ===[{base_info['invoiceNumber']}][{base_info['date']}]===> {base_info['recipientName']}")
            return base_info
        else:
            logging.error(f"Status code={response.status_code}\tmsg={response.text}")


if __name__ == '__main__':
    import credentials

    ts = TSDigital(credentials.email, credentials.password, credentials.VAT_number)
    print(ts.invoices("invoice_19.xml"))
