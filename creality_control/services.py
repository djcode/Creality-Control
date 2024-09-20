from homeassistant.core import HomeAssistant
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def handle_pause_resume_print_service(hass: HomeAssistant, call):
    entity_id = call.data.get("entity_id")
    command = call.data.get("command")
    device_registry = dr.async_get(hass)

    # Example logic to find a device and send a command
    for device in device_registry.devices.values():
        for identifier in device.identifiers:
            if DOMAIN in identifier:
                device_id = identifier[1]
                _LOGGER.debug(f"Sending command {command} to device {device_id}")
                
                # Determine the printer type and send the appropriate command
                printer_type = call.data.get("printer_type", "halot")  # Default to 'halot' if not specified
                
                if printer_type == "wifi_box":
                    success = await send_command_to_device(device_id, command)
                else:  # For Halot Resin Printer
                    success = await send_command_to_device(device_id, translate_command_for_halot(command))

                if success:
                    _LOGGER.info(f"Successfully sent {command} to {device_id}")
                else:
                    _LOGGER.error(f"Failed to send {command} to {device_id}")
                break

async def handle_stop_print_service(hass: HomeAssistant, call):
    entity_id = call.data.get("entity_id")
    command = "stop_print"  # Example command, adjust as needed
    device_registry = dr.async_get(hass)

    for device in device_registry.devices.values():
        for identifier in device.identifiers:
            if DOMAIN in identifier:
                device_id = identifier[1]
                _LOGGER.debug(f"Sending command {command} to device {device_id}")
                
                printer_type = call.data.get("printer_type", "halot")
                
                if printer_type == "wifi_box":
                    success = await send_command_to_device(device_id, command)
                else:  # For Halot Resin Printer
                    success = await send_command_to_device(device_id, translate_command_for_halot(command))
                
                if success:
                    _LOGGER.info(f"Successfully sent {command} to {device_id}")
                else:
                    _LOGGER.error(f"Failed to send {command} to {device_id}")
                break

def translate_command_for_halot(command):
    """Translate generic command names to Halot-specific commands."""
    command_map = {
        "pause_resume_print": "PRINT_PAUSE",
        "stop_print": "PRINT_STOP"
    }
    return command_map.get(command, command)

def register_services(hass: HomeAssistant):
    # Service schemas now using entity_id and printer_type
    pause_resume_print_schema = vol.Schema({
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("command"): cv.string,
        vol.Optional("printer_type", default="halot"): cv.string,
    })

    stop_print_schema = vol.Schema({
        vol.Required("entity_id"): cv.entity_id,
        vol.Optional("printer_type", default="halot"): cv.string,
    })

    hass.services.async_register(DOMAIN, "pause_resume_print", handle_pause_resume_print_service, schema=pause_resume_print_schema)
    hass.services.async_register(DOMAIN, "stop_print", handle_stop_print_service, schema=stop_print_schema)
