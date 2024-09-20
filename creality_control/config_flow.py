import voluptuous as vol
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from aiohttp import ClientSession, ClientError
import async_timeout
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad
from base64 import b64encode
from binascii import unhexlify
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

class CrealityControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Creality Control."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Test connection based on the selected printer type
            if user_input["printer_type"] == "halot":
                valid = await self._test_connection_halot(
                    user_input["host"], user_input["port"], user_input["password"]
                )
            else:  # wifi_box
                valid = await self._test_connection_wifi_box(
                    user_input["host"], user_input["port"]
                )

            if valid:
                return self.async_create_entry(title="Creality Control", data=user_input)
            else:
                errors["base"] = "cannot_connect" if valid is None else "invalid_password"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("printer_type", default="halot"): vol.In(["halot", "wifi_box"]),
                vol.Required("host"): cv.string,
                vol.Required("port", default=18188): cv.port,
                vol.Optional("password"): cv.string,
            }),
            errors=errors,
        )

    async def _test_connection_halot(self, host, port, password):
        """Test connection to the Halot printer."""
        uri = f"ws://{host}:{port}/"
        token = self.generate_token(password)
        try:
            async with ClientSession() as session:
                async with session.ws_connect(uri) as ws:
                    await ws.send_json({"cmd": "GET_PRINT_STATUS", "token": token})
                    async with async_timeout.timeout(10):
                        response = await ws.receive_json()
                        if "printStatus" in response and response["printStatus"] == "TOKEN_ERROR":
                            return False  # Token is invalid
                        return True  # Assuming any response with printStatus not TOKEN_ERROR is valid
        except Exception as e:
            return None  # Unable to connect
        return None  # In case the connection could not be established or an unexpected error occurred

    async def _test_connection_wifi_box(self, host, port):
        """Test connection to the Wi-Fi Box."""
        uri = f"http://{host}:{port}/protocal.csp?fname=Info&opt=main&function=get"
        try:
            async with ClientSession() as session:
                async with session.get(uri) as resp:                    
                    async with async_timeout.timeout(10):
                        response = await resp.text()
                        if "printProgress" not in response:
                            return False 
                        return True  # Assuming any response with printStatus is valid
        except Exception as e:
            return None  # Unable to connect
        return None  # In case the connection could not be established or an unexpected error occurred

    def generate_token(self, password):
        """Generate a token based on the password."""
        key = unhexlify("6138356539643638")
        cipher = DES.new(key[:8], DES.MODE_ECB)
        padded_password = pad(password.encode(), DES.block_size)
        encrypted_password = cipher.encrypt(padded_password)
        token = b64encode(encrypted_password).decode('utf-8')
        return token
