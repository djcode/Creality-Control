import aiohttp
import logging
import asyncio
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad
from base64 import b64encode
from binascii import unhexlify
import async_timeout
import json
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = aiohttp.ClientSession()
    coordinator = CrealityDataCoordinator(hass, session, entry.data)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ['sensor', 'button'])

    return True

class CrealityDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, session, config):
        self.session = session
        self.config = config
        self.is_offline = False  # Initialize an is_offline flag
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=30))
    
    @property
    def host(self):
        return self.config['host']

    async def _async_update_data(self):
        """Fetch data from the printer."""
        if self.config.get('printer_type') == 'wifi_box':
            return await self._fetch_data_wifi_box()
        else:
            return await self._fetch_data_halot()

    async def _fetch_data_halot(self):
        """Fetch data from the Halot printer."""
        uri = f"ws://{self.config['host']}:{self.config['port']}/"
        token = self.generate_token(self.config['password'])

        _LOGGER.debug(f"Attempting to connect to WebSocket at {uri}")
        try:
            async with self.session.ws_connect(uri) as ws:
                await ws.send_json({"cmd": "GET_PRINT_STATUS", "token": token})
                response = await ws.receive_json()
                _LOGGER.debug(f"Received response: {response}")
                if response:
                    self.is_offline = False  # Set is_offline to False if successful
                    _LOGGER.info(f"Successfully fetched data: {response}")
                    return response
                else:
                    _LOGGER.error("Failed to receive data")
                    return {}
        except Exception as e:
            self.is_offline = True  # Set is_offline to True if an error occurs
            _LOGGER.error(f"Error fetching data: {e}")
            return {}

    async def _fetch_data_wifi_box(self):
        """Fetch data from the Wi-Fi Box."""
        uri = f"http://{self.config['host']}:{self.config['port']}/protocal.csp?fname=Info&opt=main&function=get"
        try:
            async with self.session.get(uri) as resp:
                async with async_timeout.timeout(10):
                    txt = await resp.text()
                    msg = json.loads(txt)
                    if msg:
                        return msg
                    else:
                        _LOGGER.error("Failed to receive data")
                        return None
        except Exception as e:
            _LOGGER.error(f"Error fetching data: {e}")
            return None

    async def send_command(self, command):
        """Send command to the Creality printer using the stored session and config."""
        if self.config.get('printer_type') == 'wifi_box':
            await self._send_command_wifi_box(command)
        else:
            await self._send_command_halot(command)

    async def _send_command_halot(self, command):
        """Send a command to the Halot printer."""
        if self.is_offline:  # Check if the printer is offline before attempting to send a command
            _LOGGER.error(f"Cannot send command '{command}': Printer is offline.")
            return

        uri = f"ws://{self.config['host']}:{self.config['port']}/"
        token = self.generate_token(self.config['password'])
        try:
            async with self.session.ws_connect(uri) as ws:
                await ws.send_json({"cmd": command, "token": token})
                response = await ws.receive_json()
                if response.get("status") == "ok":
                    _LOGGER.info(f"Successfully sent command {command}")
                else:
                    _LOGGER.error(f"Failed to send command {command}: {response}")
        except Exception as e:
            _LOGGER.error(f"Error sending command {command}: {e}")

    async def _send_command_wifi_box(self, command):
        """Send a command to the Wi-Fi Box printer."""
        uri = ""
        if command == "PRINT_STOP":
            uri = f"http://{self.config['host']}:{self.config['port']}/protocal.csp?fname=net&opt=iot_conf&function=set&stop=1"
        elif command == "PRINT_PAUSE":
            uri = f"http://{self.config['host']}:{self.config['port']}/protocal.csp?fname=net&opt=iot_conf&function=set&pause=1"
        elif command == "PRINT_RESUME":
            uri = f"http://{self.config['host']}:{self.config['port']}/protocal.csp?fname=net&opt=iot_conf&function=set&pause=0"
        try:
            async with self.session.get(uri) as resp:
                async with async_timeout.timeout(10):
                    txt = await resp.text()
                    msg = json.loads(txt)
                    if msg.get("error") == "0":
                        _LOGGER.info(f"Command {command} executed successfully.")
                    else:
                        _LOGGER.error(f"Command {command} failed.")
        except Exception as e:
            _LOGGER.error(f"Failed to send command {command}: {e}")

    def generate_token(self, password):
        """Generate a token for device authentication."""
        key = unhexlify("6138356539643638")
        cipher = DES.new(key, DES.MODE_ECB)
        padded_password = pad(password.encode(), DES.block_size)
        encrypted_password = cipher.encrypt(padded_password)
        return b64encode(encrypted_password).decode('utf-8')
        
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info(f"Creality Control integration unloaded: {entry.title}")
    return await hass.config_entries.async_unload_platforms(entry, ["sensor", "button"])
