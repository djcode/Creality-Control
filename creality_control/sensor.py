from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import Entity
from datetime import datetime, timedelta
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Creality Control sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = []

    # Check the printer type to populate the appropriate sensors
    if entry.data.get("printer_type") == "wifi_box":
        sensors.extend([
            CrealitySensor(coordinator, "wanip", "IP Address"),
            CrealitySensor(coordinator, "state", "Current State"),
            CrealitySensor(coordinator, "printProgress", "Job Percentage", unit_of_measurement="%"),
            CrealityTimeSensor(coordinator, "printJobTime", "Time Running"),
            CrealityTimeSensor(coordinator, "printLeftTime", "Time Left"),
            CrealitySensor(coordinator, "completionTime", "Completion Time"),        
            CrealitySensor(coordinator, "print", "Filename"),
            CrealitySensor(coordinator, "nozzleTemp", "Nozzle Temp"),
            CrealitySensor(coordinator, "bedTemp", "Bed Temp"),
            CrealitySensor(coordinator, "err", "Error"),
            CrealitySensor(coordinator, "upgradeStatus", "Upgrade Available"),
        ])
    else:  # Default to your original Halot resin printer sensors
        sensors.extend([
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
            CrealitySensor(coordinator, "printStatusFriendly", "Status")
        ])

    async_add_entities(sensors)

class CrealitySensor(CoordinatorEntity, Entity):
    """Defines a single Creality sensor."""

    def __init__(self, coordinator, data_key, name_suffix, unit_of_measurement=None):
        super().__init__(coordinator)
        self.data_key = data_key
        self._attr_name = f"{coordinator.config.get('model', 'Creality')} {name_suffix}"
        self._attr_unique_id = f"{coordinator.config['host']}_{data_key}"
        self._unit_of_measurement = unit_of_measurement

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._attr_name

    @property
    def unique_id(self):
        """Return a unique identifier for this sensor."""
        return self._attr_unique_id

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement if defined."""
        return self._unit_of_measurement

    @property
    def device_info(self):
        """Return information about the device this sensor is part of."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.config['host'])},
            "name": "Creality Printer",
            "manufacturer": "Creality",
            "model": self.coordinator.config.get('model', 'Creality Printer'),
        }

    @property
    def state(self):
        """Return the state of the sensor."""
        # Halot-specific sensor handling
        if self.coordinator.config.get("printer_type") != "wifi_box":
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

        # Wi-Fi Box-specific sensor handling
        if self.data_key == "state":
            state = self.coordinator.data.get("state", 0)
            connect = self.coordinator.data.get("connect", 0)        
            if connect == 2:
                return "Offline"
            if state == 1:
                return "Printing"
            if state == 2:
                return "Idle"
            if state == 4:
                return "Error"
            return "Unable to parse status"
        
        if self.data_key == "err":
            error = self.coordinator.data.get("err", 0)
            if error == 0:
                return "No"
            return "Yes"

        if self.data_key == "upgradeStatus":
            upgradeStatus = self.coordinator.data.get("upgradeStatus", 0)
            if upgradeStatus == 0:
                return "No"
            return "Yes"

        if self.data_key == "completionTime":
            printTimeLeft = self.coordinator.data.get("printLeftTime", 0)
            today = datetime.now()
            completion = today + timedelta(0, printTimeLeft)
            return completion.strftime("%m-%d-%Y %H:%M")

        # Generic state for all other sensors
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

class CrealityTimeSensor(CrealitySensor):
    """Specialized sensor class for handling 'Time' data for Wi-Fi Box."""

    @property
    def state(self):
        """Return the state of the sensor, converting time to HH:MM:SS format."""
        time_left = int(self.coordinator.data.get(self.data_key, 0))
        return str(timedelta(seconds=time_left))

async def _async_update_data(self):
    """Fetch data from the printer."""
    _LOGGER.debug(f"Fetching data from the printer at {self.host}")
    # Fetch the data here
    data = await self.fetch_data()
    _LOGGER.debug(f"Fetched data: {data}")
    return data
