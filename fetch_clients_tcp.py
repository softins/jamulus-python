#!/usr/bin/env python3

import jamulus

import argparse
import signal
import sys

from time import time


def format_client(client):
    return "{:>3} {:<20} {:<20} {:<12} {:<20} {:<20}".format(
        client.get("id", "?"),
        client.get("name", "?"),
        jamulus.INSTRUMENT_KEYS.get(client.get("instrument"), "?"),
        jamulus.SKILL_KEYS.get(client.get("skill"), "?"),
        client.get("city", "?"),
        jamulus.COUNTRY_KEYS.get(client.get("country"), "?"),
    )

def format_server(server):
    age_seconds = int(time() - server["time_updated"]) if "time_updated" in server.keys() else "?"
    return "{:>15}:{:<5} {} {:<20} {:>3}/{:<3} {}/{} ({}/{}) {}s {}".format(
        server.get("ip", 0),
        server.get("port", 0),
        "*" if server.get("permanent", 0) == 1 else " ",
        server.get("name", "?"),
        server.get("clients", "?"),
        server.get("max_clients", "?"),
        server.get("city", "?"),
        jamulus.COUNTRY_KEYS.get(server.get("country_id"), "?"),
        jamulus.OS_KEYS.get(server.get("os"), "?"),
        server.get("version", "?"),
        age_seconds,
        server.get("internal_address", ""),
    )

def argument_parser():
    parser = argparse.ArgumentParser()
    # use default port 0 for a client
    parser.add_argument("--port", type=int, default=0, help="local port number")
    parser.add_argument(
        "--server",
        type=jamulus.server_argument,
        required=True,
        action="extend",
        nargs="+",
        default=[],
        help="servers for fetching client list",
    )
    parser.add_argument(
        "--log-data",
        action="store_true",
        help="log protocol data",
    )
    return parser.parse_args()


################################################################################


def main():
    # get arguments
    args = argument_parser()

    timeout = 3

    # create jamulus connector
    jc = jamulus.JamulusConnector(port=args.port, log_data=args.log_data, tcp=True)

    for addr in args.server:
        jc.connect(addr, timeout=2)
        jc.sendto(addr, "CLM_REQ_CONN_CLIENTS_LIST")

    # receive messages indefinitely
    while True:

        try:
            addr, key, count, values = jc.recvfrom(timeout)
        except TimeoutError:
            break
            #continue

        if key == "AUDIO":
            # stop clients from connecting
            jc.sendto(addr, "CLM_DISCONNECTION")

        elif key == "CLM_CONN_CLIENTS_LIST":
            # client list received
            print("received {} clients".format(len(values)))
            for client in values:
                print(format_client(client))
            #break

        elif key == "CLM_SERVER_LIST":
            # server list received
            print("received {} servers".format(len(values)))
            for server in values:
                print(format_server(server))
            #break


def signal_handler(sig, frame):
    print()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
