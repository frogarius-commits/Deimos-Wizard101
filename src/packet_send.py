import binascii
import os
import subprocess
import json
import asyncio
import random
from wizwalker.client import Client
from wizwalker import XYZ
from wizwalker.memory.memory_objects.enums import Enum, MagicSchool

from loguru import logger

def binToText(hex_str: str):
    try:
        hex_bytes = binascii.unhexlify(hex_str.replace(" ", ""))
    except binascii.Error as e:
        logger.warning(e)
        return hex_str
    except AttributeError:
        return None
    
    ascii_str = ''.join(chr(byte) if 32 <= byte <= 126 else '.' for byte in hex_bytes)
    # ....).........c.x`.........~].g..NoAggro method worked for NoAggro/Equip/friend tp
    reversed_str = ascii_str[::-1]
    
    last_word = reversed_str.split('.')[0]
    
    last_word = last_word[::-1]
    # returned last word but decided to use ascii_str
    return ascii_str

class NetPackError(Exception):
    """Base class for custom exceptions in this module."""
    pass

async def send_packets(client: Client, debug: bool = False):
    try:
        
        json_path = os.path.abspath("sender.json")
        command = ["Sender.exe", "--json-file", json_path]
        
        global process
        # command = ["Sender.exe", "--json-file", "sender.json"]
        
        logger.info(f"Starting process with args: {' '.join(command)}")
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(json_path),
            shell=True
        )
        
        for line in process.stdout:
            logger.info(line.strip())
        
        for line in process.stderr:
            logger.error(line.strip())
        
        process.wait()
        logger.info("Delivered :)")
    
    except Exception as e:
        logger.error(f"Error sending packets: {e}")

async def send_cantrip_packet(client, client_gid: int, target_gid: int, school: Enum, location: XYZ, phase: int = 1): 
    try:
        print(f"Sending cantrip packet to {target_gid} with school {school} at location {location} for client {client_gid}.")
        packet = {
            "MSG_CASTRITUAL": {
                "CasterGID": {
                    "value": client_gid,
                    "type": "GID"
                },
                "SpellTemplateID": {
                    "value": 2004118039,
                    "type": "INT"
                },
                "TargetObjectID": {
                    "value": target_gid,
                    "type": "GID"
                },
                "TargetX": {
                    "value": location.x,
                    "type": "FLT"
                },
                "TargetY": {
                    "value": location.y,
                    "type": "FLT"
                },
                "TargetZ": {
                    "value": location.z,
                    "type": "FLT"
                },
                "SchoolID": {
                    "value": school.value,
                    "type": "UINT"
                },
                "Phase": {
                    "value": phase,
                    "type": "UBYT"
                },
                "from_server": False,
                "service_name": "CantripsMessages"
            }
        }

        # write out the packet JSON
        JSON_PATH = "sender.json"
        with open(JSON_PATH, "w") as f:
            json.dump(packet, f, indent=4)

        # dispatch it via Sender.exe
        await send_packets(client, debug=True)
    except Exception as e:
        print(e)