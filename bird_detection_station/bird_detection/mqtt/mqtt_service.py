import logging
from abc import ABC, abstractmethod

import paho.mqtt.client as mqtt  # type: ignore

import ssl


class MQTTServiceInterface(ABC):
    @abstractmethod
    def publish(self, topic, payload):
        pass


class MQTTSSLConfig:
    def __init__(
        self,
        ca: str = "mqtt-client/ca.crt",
        cert: str = "mqtt-client/client.crt",
        private: str = "mqtt-client/client.key",
    ):
        self.ca = ca
        self.cert = cert
        self.private = private


def ssl_alpn(mqtt_ssl_config: MQTTSSLConfig):
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.load_verify_locations(cafile=mqtt_ssl_config.ca)
        ssl_context.load_cert_chain(
            certfile=mqtt_ssl_config.cert, keyfile=mqtt_ssl_config.private
        )
        return ssl_context
    except Exception as e:
        logging.warning("exception ssl_alpn()")
        raise e


class MQTTService(MQTTServiceInterface):
    def __init__(
        self,
        mqtt_broker: str,
        mqtt_server_port: int,
        use_ssl: bool = False,
        mqtt_ssl_config: MQTTSSLConfig = MQTTSSLConfig(),
    ):

        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        if use_ssl:
            self.mqtt_ssl_config = mqtt_ssl_config
            ssl_context = ssl_alpn(self.mqtt_ssl_config)
            self.client.tls_set_context(context=ssl_context)

        try:
            self.client.connect(mqtt_broker, mqtt_server_port, 60)
        except ConnectionRefusedError:
            print("Could not connect to MQTT broker")

        self.client.loop_start()

    @staticmethod
    def _on_connect(client, userdata, flags, rc):
        logging.info("Connected with result code " + str(rc))

    @staticmethod
    def _on_message(client, userdata, msg):
        logging.info(msg.topic + " " + str(msg.payload))

    def publish(self, topic, payload):
        self.client.publish(topic, payload, qos=0, retain=False)
