from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import Entity
from datetime import timedelta
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = [
        CrealitySensor(coordinator, "printStatus", "Printer Status"),
        CrealitySensor(coordinator, "filename", "Filename"),
        CrealityTimeLeftSensor(coordinator, "printRemainTime", "Time Left"),
        CrealitySensor(coordinator, "progress", "Progress", unit_of_measurement="%"),
        CrealitySensor(coordinator, "curSliceLayer", "Current Layer"),
        CrealitySensor(coordinator, "sliceLayerCount", "Total Layers"),
        CrealitySensor(coordinator, "printExposure", "Print Exposure", unit_of_measurement="s"),
        CrealitySensor(coordinator, "layerThickness", "Layer Thickness", unit_of_measurement="mm"),
        CrealitySensor(coordinator, "printHeight", "Rising Height", unit_of_measurement="mm"),
        CrealitySensor(coordinator, "bottomExposureNum", "Bottom Layers"),
        CrealitySensor(coordinator, "initExposure", "Initial Exposure", unit_of_measurement="s"),
        CrealitySensor(coordinator, "delayLight", "Turn off Delay", unit_of_measurement="s"),
        CrealitySensor(coordinator, "eleSpeed", "Motor Speed", unit_of_measurement="mm/s"),
        CrealitySensor(coordinator, "resin", "Resin"),
    ]
    sensors.append(CrealitySensor(coordinator, "printStatusFriendly", "Status"))
    async_add_entities(sensors)

class CrealitySensor(CoordinatorEntity, Entity):
    """Defines a single Creality sensor."""

    def __init__(self, coordinator, data_key, name_suffix, unit_of_measurement=None):
        super().__init__(coordinator)
        self.data_key = data_key
        self._attr_name = f"Creality {name_suffix}"
        self._attr_unique_id = f"{coordinator.host}_{data_key}"
        self._unit_of_measurement = unit_of_measurement

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config['host'])},
            "name": "Creality Printer",
            "manufacturer": "Creality",
            "model": "Creality Printer",
        }
        
    @property
    def state(self):
        """Return the state of the sensor."""
        # Handle the offline status first
        if self.coordinator.is_offline:
            return "Offline"
        
        # Handle the special case for the friendly status
        if self.data_key == "printStatusFriendly":
            raw_status = self.coordinator.data.get("printStatus", "Unknown")
            # Map raw status to friendly status
            status_map = {
                "PRINT_STOP": "Paused/Stopped",
                "PRINT_PROCESSING": "Printing",
                "PRINT_GENERAL": "Online",
                "PRINT_COMPLETE": "Completed",
                "Unknown": "Offline",
            }
            return status_map.get(raw_status, "Offline")

        # Handle the progress calculation
        if self.data_key == "progress":
            cur_layer = self.coordinator.data.get("curSliceLayer", 0)
            total_layers = self.coordinator.data.get("sliceLayerCount", 0)
            try:
                progress = (float(cur_layer) / float(total_layers)) * 100 if total_layers else 0
                return round(progress, 2) if total_layers else 0
            except ValueError:
                return 0
        
        # Return the generic state for all other sensors
        return self.coordinator.data.get(self.data_key, "Unknown")


class CrealityTimeLeftSensor(CrealitySensor):
    """Specialized sensor class for handling 'Time Left' data."""

    @property
    def state(self):
        """Return the state of the sensor, converting time to HH:MM:SS format or indicating not available."""
        if self.coordinator.is_offline:
            return "Not Available"
        raw_time_left = self.coordinator.data.get(self.data_key, "")
        if raw_time_left.isdigit():
            time_left = int(raw_time_left)
            return str(timedelta(seconds=time_left))
        _LOGGER.info(f"Received invalid data for time left: '{raw_time_left}'. Returning 'Not Available'.")
        return "Not Available"