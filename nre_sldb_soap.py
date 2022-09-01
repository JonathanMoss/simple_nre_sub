"""Create and maintains a connection to NRE SLDB"""

import os
import time
from datetime import datetime
import schedule
from zeep import Client, Settings
from zeep import xsd
from zeep.plugins import HistoryPlugin
from persistent_outbound_mq import OutboundMqConnection


TIPLOCS = os.getenv('TIPLOCS', ())
LDB_TOKEN = os.getenv('SLDB_TOKEN')
WSDL = os.getenv('SLDB_WSDL')
CHECK_FREQ = int(os.getenv('SLDB_FREQ'))
RMQ_EXCHANGE = os.getenv('SLDB_RMQ_EXCHANGE')

if None in (LDB_TOKEN, WSDL, CHECK_FREQ, RMQ_EXCHANGE):
    MSG = "Missing environment variables"
    raise Exception(MSG)

class SoapConnection(OutboundMqConnection):
    """Fetch the LDB Data"""

    instances = []

    def __init__(self, tiploc: str):
        """Initialisation"""

        self.new_lnk = tiploc
        super().__init__(RMQ_EXCHANGE)

        self.instances.append(self)

    def fetch(self) -> dict:
        """Fetch the data"""

        time_now = str(
            datetime.now().replace(second=0, microsecond=0).time()
        )

        history = HistoryPlugin()
        client = Client(wsdl=WSDL, plugins=[history], settings=Settings(strict=False))
        header = xsd.Element(
            '{http://thalesgroup.com/RTTI/2013-11-28/Token/types}AccessToken',
            xsd.ComplexType([
                xsd.Element(
                    '{http://thalesgroup.com/RTTI/2013-11-28/Token/types}TokenValue',
                    xsd.String()),
            ])
        )
        header_value = header(TokenValue=LDB_TOKEN)

        return client.service.GetArrivalDepartureBoardByTIPLOC(
            time=time_now,
            timeWindow=120,
            numRows=100,
            tiploc=self.new_lnk,
            _soapheaders=[header_value]
        )

    @staticmethod
    def format_time(val) -> str:
        """Takes a value, returns a string"""

        if isinstance(val, datetime):
            return str(val.time())

        return ""

    def post_to_broker(self, data: dict):  # pylint: disable=R0914
        """Post to the RMQ Broker"""

        post_list = []

        for svc in data.trainServices.service:

            # Extrapolate the TOC details
            toc_short = svc['operatorCode']
            toc_long = svc['operator']
            toc = f'<span style="cursor: pointer" title="{toc_long}">'
            toc += f'{toc_short}</span>'

            # Extrapolate origin
            org_tpl = svc['origin']['location'][0]['tiploc']
            org_desc = svc['origin']['location'][0]['locationName']
            origin = f'<span style="cursor: pointer;" title="{org_desc}">'
            origin += f'{org_tpl}</span>'

            # Extrapolate destination
            dest_tpl = svc['destination']['location'][0]['tiploc']
            dest_desc = svc['destination']['location'][0]['locationName']
            destination = f'<span style="cursor: pointer;" title="{dest_desc}">'
            destination += f'{dest_tpl}</span>'

            # Extrapolate Platform
            hidden = svc['platformIsHidden']
            platform = svc['platform']
            if not platform or hidden:
                platform = "TBC"

            # Arrival Times
            sta = self.format_time(svc['sta'])
            eta = self.format_time(svc['eta'])

            # Departure Times
            std = self.format_time(svc['std'])
            etd = self.format_time(svc['etd'])

            # Consist
            consist = ""
            length = svc['length']
            if length:
                consist = f"Service consists of {length} vehicles"

            svc_data = {
                'headcode': svc['trainid'],
                'uid': svc['uid'],
                'toc': toc,
                'consist': consist,
                'origin': origin,
                'destination': destination,
                'platform': platform,
                'wta': sta,
                'wtd': std,
                'eta': eta,
                'etd': etd,
                'last_reported': "",
                'distruption': "",
                'cis_comments': ""
            }

            print(svc_data)

            post_list.append(svc_data)


        self.send_msg(
            {'results': post_list},
            headers={
                'tiploc': self.new_lnk
            }
        )

    @staticmethod
    def get_update():
        """For each instance, fetch the data and post on the broker"""

        for instance in SoapConnection.instances:
            data = instance.fetch()

            instance.post_to_broker(data)


if __name__ == "__main__":

    for entry in TIPLOCS.split(','):
        SoapConnection(entry)

    schedule.every(CHECK_FREQ).seconds.do(SoapConnection.get_update)

    while True:
        schedule.run_pending()
        time.sleep(1)
