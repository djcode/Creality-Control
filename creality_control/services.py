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
    # This is a placeholder and needs to be adapted to your integration's specifics
    for device in device_registry.devices.values():
        for identifier in device.identifiers:
            if DOMAIN in identifier:
                device_id = identifier[1]  # Assuming the device ID is the second element
                _LOGGER.debug(f"Sending command {command} to device {device_id}")
                # Replace the next line with the actual command sending logic
                success = await send_command_to_device(device_id, command)
                if success:
                    _LOGGER.info(f"Successfully sent {command} to {device_id}")
                else:
                    _LOGGER.error(f"Failed to send {command} to {device_id}")
                break

async def handle_stop_print_service(hass: HomeAssistant, call):
    # Implement similarly to handle_pause_resume_print_service

def register_services(hass: HomeAssistant):
    # Service schemas now using entity_id
    pause_resume_print_schema = vol.Schema({
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("command"): cv.string,
    })

    stop_print_schema = vol.Schema({
        vol.Required("entity_id"): cv.entity_id,
    })

    hass.services.async_register(DOMAIN, "pause_resume_print", handle_pause_resume_print_service, schema=pause_resume_print_schema)
    hass.services.async_register(DOMAIN, "stop_print", handle_stop_print_service, schema=stop_print_schema)