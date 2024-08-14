"""RZBuddy & IoTConnect Integration"""

import json
import socket
import sys
import signal
import time
from datetime import datetime
from typing import Dict, Any, List

from iotconnect import IoTConnectSDK
import servo_controller.servo_manager as servo_manager


class SignalException(Exception):
    """Custom exception to exit gracefully"""


class IoTConnectManager:
    """Send RZBuddy data to IoTConnect platform using IoTConnect SDK."""

    def __init__(self, configs: List[str]) -> None:
        self.config = {}
        self.inject_config(configs)
        print(f"Configuration loaded: {self.config}")

        self.sdk = None
        self.device_list = []
        self.setup_exit_handler()

        print("Initializing GPIO")
        self.gpio_init_healthy = servo_manager.init_gpio()
        if self.gpio_init_healthy:
            print("GPIO initialized")
        else:
            print(
                "GPIO initialization failed! Servo will not rotate, but \
                telemetry may still work. Continuing...")

        self.run_continuously = True
        self.last_payload_str = None
        self.next_transmit_time = time.time()
        print("IoTConnect Manager initialized. Ready to start IoTConnect connection.")

    def inject_config(self, config_paths: List[str]) -> None:
        """Inject app configuration, dependencies"""
        try:
            for config_path in config_paths:
                with open(config_path, encoding="utf-8") as f:
                    # Load configuration from JSON file(s) with UNIQUE KEYS
                    self.config.update(json.load(f))
        except Exception as e:
            print(f"Error injecting config: {e}")
            sys.exit(1)

    # WARN: Not in use for now
    def get_dgram_socket(self) -> socket.socket:
        """Attempt connection (continuously) to RZBuddy producer socket"""
        raise NotImplementedError("This method is not in use for now")

        max_retry_backoff_s = 8
        retry_backoff_s = 1
        sock = None
        while self.run_continuously:
            try:
                for addr in socket.getaddrinfo(self.config['rzbuddy_socket_ipv6'], self.config['rzbuddy_socket_port'], socket.AF_INET6, socket.SOCK_DGRAM, 0, socket.AI_PASSIVE):
                    af, socktype, proto, _, sa = addr
                    try:
                        sock = socket.socket(af, socktype, proto)
                        sock.setsockopt(socket.SOL_SOCKET,
                                        socket.SO_REUSEADDR, 1)
                    except OSError as msg:
                        print(f"Socket init failed: {msg}. Retrying...")
                        sock = None
                        continue
                    try:
                        sock.bind(sa)
                    except OSError as msg:
                        print(f"Socket bind failed: {msg}. Retrying...")
                        sock.close()
                        sock = None
                        continue
                    # Success
                    break

                if sock is None:
                    raise ConnectionError("Failed to create socket")

                return sock
            except SignalException:
                sys.exit(0)
            except Exception as msg:
                retry_backoff_s = min(max_retry_backoff_s, retry_backoff_s * 2)
                time.sleep(retry_backoff_s)

    def setup_exit_handler(self) -> None:
        """Define exit conditions as application will typically run indefinitely"""
        signal.signal(signal.SIGINT, self.exit_handler)
        signal.signal(signal.SIGTERM, self.exit_handler)

    def exit_handler(self, _sig, _frame) -> None:
        """Stop IoT/RZBuddy integration"""
        print("Exit signal detected. Exiting...")
        self.run_continuously = False
        raise SignalException("Exit signal detected")

    # WARN: Not in use for now
    def receive_json_payload(self, sock: socket.socket) -> Dict[str, Any]:
        """Receive JSON payload from producer socket"""
        raise NotImplementedError("This method is not in use for now")

        if sock is None:
            raise ConnectionError("RZBuddy consumer socket not connected")

        bytes_data, _ = sock.recvfrom(1024)
        if not bytes_data:
            raise ConnectionError("RZBuddy producer socket closing")

        try:
            return json.loads(bytes_data.decode('utf-8'))
        except Exception as e:
            print(f"Failed to parse JSON payload: {e}")
            return dict()

    def device_command_callback(self, msg: Dict[str, Any]) -> None:
        print("\n--- Device Callback ---")
        print(json.dumps(msg))
        cmd_type = None
        if msg is not None and len(msg.items()) != 0:
            cmd_type = msg["ct"] if "ct" in msg else None
        # Other Command
        if cmd_type == 0:
            """
            * Type    : Public Method "sendAck()"
            * Usage   : Send device command received acknowledgment to cloud
            * 
            * - status Type
            *     st = 6; // Device command Ack status 
            *     st = 4; // Failed Ack
            * - Message Type
            *     msgType = 5; // for "0x01" device command 
            """
            data = msg
            if data is None:
                # print(data)
                if "id" in data:
                    if "ack" in data and data["ack"]:
                        # fail=4,executed= 5,sucess=7,6=executedack
                        self.sdk.sendAckCmd(
                            data["ack"], 7, "sucessfull", data["id"])
                else:
                    if "ack" in data and data["ack"]:
                        # fail=4,executed= 5,sucess=7,6=executedack
                        self.sdk.sendAckCmd(data["ack"], 7, "sucessfull")
        else:
            print("rule command", msg)

        # TODO: Extract rotation count
        if self.gpio_init_healthy:
            try:
                servo_manager.perform_full_rotations(1)
            except Exception as e:
                print(f"Error performing servo rotation: {e}. Continuing...")
        else:
            print("GPIO initialization failed. Skipping servo rotation.")

    def device_firmware_callback(self, msg: Dict[str, Any]) -> None:
        print("\n--- Firmware Command Message Received ---")
        print("--- No further business logic implemented ---")
        print(json.dumps(msg))

    def device_connection_callback(self, msg: Dict[str, Any]) -> None:
        print(
            "\n--- Device coonnection callback: no further business logic implemented ---")
        print(json.dumps(msg))

    def twin_update_callback(self, msg: Dict[str, Any]) -> None:
        print("--- Twin Message Received ---")
        print("--- No further business logic implemented ---")
        print(json.dumps(msg))

    def send_json_payload_throttled(self, feed_data: Dict[str, Any]) -> bool:
        """Send JSON payload to IoTConnect"""
        if feed_data is None or len(feed_data.items()) == 0:
            print("Empty payload. Skipping transmission.")
            return False

        try:
            # Snapshot payload before altering it
            cur_payload_str = json.dumps(feed_data)
            # Maybe we want to send the same data multiple times if lots of time has passed
            if cur_payload_str == self.last_payload_str or time.time() < self.next_transmit_time:
                return False

            payload = [{
                "uniqueId": self.config['ids']['uniqueId'],
                "time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "data": feed_data
            }]
            print(f"Sending payload: {payload}")
            self.sdk.SendData(payload)

            self.last_payload_str = cur_payload_str
            self.next_transmit_time = time.time(
            ) + self.config['transmit_interval_seconds']
            return True

        except Exception as e:
            print(f"Caught exception \
                {e} while trying to send JSON payload to IoT connect.")
            return False

    def run_telemetry_continuously(self) -> None:
        """Run IoTConnect client continuously"""
        max_retry_backoff_s = 300
        retry_backoff_s = 5
        while self.run_continuously:
            try:
                print("Starting IoTConnect SDK")
                with IoTConnectSDK(self.config['ids']['uniqueId'],
                                   self.config['ids']['sid'],
                                   self.config['sdk_options'],
                                   self.device_connection_callback
                                   ) as self.sdk:

                    self.device_list = self.sdk.Getdevice()
                    self.sdk.onDeviceCommand(self.device_command_callback)
                    self.sdk.onTwinChangeCommand(self.twin_update_callback)
                    self.sdk.onOTACommand(self.device_firmware_callback)
                    self.sdk.onDeviceChangeCommand(
                        self.device_connection_callback)
                    self.sdk.getTwins()
                    self.device_list = self.sdk.Getdevice()

                    print("IoTConnect SDK configured. Connected to IoTConnect.")

                    # rzbuddy_socket = self.get_dgram_socket()
                    # print("Forwarding telemetry data to IoTConnect when it arrives...")
                    while True:
                        #    payload = self.receive_json_payload(rzbuddy_socket)
                        payload = {"status": "no dog detected",
                                   "todays_total_dispense": 0,
                                   "treat_dispense":
                                   datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")}
                        self.send_json_payload_throttled(payload)
            except SignalException:
                sys.exit(0)
            # exponential backoff
            except Exception as ex:
                print(f'Backing off from exception: {ex}')
                time.sleep(retry_backoff_s)
                retry_backoff_s = min(max_retry_backoff_s, retry_backoff_s * 2)


if __name__ == "__main__":
    client = IoTConnectManager(
        ['config/iotconnect-config-secrets.json',
         'config/network_config.json'])
    client.run_telemetry_continuously()
