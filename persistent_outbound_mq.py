#!/usr/bin/env python3
"""Module for a persistent RabbitMQ outbound connection"""

import json
import os
import sys
import time
import logging
import pika

HEARTBEAT = 30
TIMEOUT = 300
EXPIRE = '100000'
V_HOST = '/'
MAX_RETRY = 5

LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"


class OutboundMqConnection:
    """This class sends messages to the RabbitMQ Broker"""

    def __init__(self, exchange: str, logger_obj=None):
        """Initialisation"""

        self.LG = self.setup_logger(logger_obj)
        self._exchange = exchange

        self._broker_host, self._broker_port = self.get_broker_details()

        self._channel = None
        self._connection = None

    def setup_logger(self, logger_obj) -> object:
        """Returns a logger based on the one passed at init, or a default"""

        if not logger_obj:
            logging.basicConfig(
                stream=sys.stdout,
                format=LOG_FORMAT,
                level=logging.INFO
            )
            return logging.getLogger()

        return logger_obj


    def get_properties(self, headers=None) -> pika.BasicProperties:
        """Returns an object representing send message properties"""

        if isinstance(headers, dict):
            return pika.BasicProperties(
                expiration=EXPIRE,
                headers=headers
            )

        return pika.BasicProperties(
            expiration=EXPIRE
        )

    def get_params(self) -> pika.ConnectionParameters:
        """Returns an object representing connection parameters"""

        return pika.ConnectionParameters(
            host=self._broker_host,
            port=int(self._broker_port),
            virtual_host=V_HOST,
            credentials=self.get_credentials(),
            heartbeat=HEARTBEAT,
            blocked_connection_timeout=TIMEOUT
        )

    def get_broker_details(self) -> tuple:
        """Returns the broker host/port from env variables"""

        broker_host = os.environ.get('BROKER_HOST', None)
        broker_port = os.environ.get('BROKER_PORT', 5672)

        if not broker_host:
            raise ValueError('Broker host variable not set')

        return broker_host, broker_port

    def get_credentials(self) -> pika.PlainCredentials:
        """Returns the credentials for use with a broker connection"""

        rmq_user = os.environ.get('RMQ_USER', None)
        rmq_pass = os.environ.get('RMQ_PASS', None)

        if None in (rmq_user, rmq_pass):
            raise ValueError('Credentials not set in environment variables')

        return pika.PlainCredentials(
            username=rmq_user,
            password=rmq_pass
        )

    def create_connection(self) -> bool:
        """Creates a connection to RMQ"""

        self._channel = None
        self._connection = None

        try:
            self._connection = pika.BlockingConnection(self.get_params())
            self._channel = self._connection.channel()
            self._channel.exchange_declare(
                exchange=self._exchange,
                exchange_type='fanout',
                durable=True
            )
            return True
        except Exception as err:
            self.LG.error('Could not create a connection to RMQ')
            self.LG.error(f'{err}')
            return False

    def close_connection(self) -> None:
        """Correctly close the connection"""

        try:
            self._channel.close()
            self._connection.close()
            self.LG.info('Channel and Connection closed')
        except Exception as err:
            self.LG.info('Cannot gracefully close the connection')
            self.LG.info(f'{err}')
        finally:
            self._channel = None
            self._connection = None

    def publish_message(self, msg: str, headers: dict) -> bool:
        """Publish the message to the exchange"""

        try:
            self._channel.basic_publish(
                body=msg,
                exchange=self._exchange,
                routing_key='',
                properties=self.get_properties(headers)
            )

            return True

        except Exception as err:
            self.LG.error('Could not send message to RabbitMQ')
            self.LG.error(f'{err}')
            return False

    def send_msg(self, msg: dict, headers=None, raw=False, attempt=1) -> bool:
        """ This function publishes the msg to the broker """

        if not self._channel or not self._channel.is_open:
            self.create_connection()

        if not raw:
            msg = json.dumps(msg)

        if not self.publish_message(msg, headers):

            self.close_connection()
            self.LG.error(
                'Unable to publish message to RMQ'
            )

            if attempt > MAX_RETRY:
                self.LG.error(
                    'Maximum sending attempts breached, giving up...'
                )

                return False

            self.send_msg(msg, headers=headers, raw=True, attempt=(attempt + 1))

        return True

if __name__ == '__main__':

    conn = OutboundMqConnection('test')
    print(conn.send_msg({'test': 'test1'}))
    while True:
        time.sleep(2)
        print(conn.send_msg({'test': 'test1'}))
