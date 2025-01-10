from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import Entity
from datetime import timedelta
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Creality Control sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = [
        CrealitySensor(coordinator, "printFileName", "Filename"),
        CrealitySensor(coordinator, "printLeftTime", "Time Left"),
        CrealitySensor(coordinator, "printJobTime", "Time on job"),
        CrealitySensor(coordinator, "printStartTime", "Start time of print"),
        CrealitySensor(coordinator, "printProgress", "Progress", unit_of_measurement="%"),
        CrealitySensor(coordinator, "curPosition", "Position"),
        CrealitySensor(coordinator, "usedMaterialLength", "Used material in print"),
        CrealitySensor(coordinator, "TotalLayer", "Layers in print"),
        CrealitySensor(coordinator, "layer", "Current layer in print"),
        CrealitySensor(coordinator, "nozzleTemp", "Nozzle temperature", unit_of_measurement="°C"),
        CrealitySensor(coordinator, "bedTemp0", "Bed temperature", unit_of_measurement="°C"),
        CrealitySensor(coordinator, "boxTemp", "Box temperature", unit_of_measurement="°C"),
        CrealitySensor(coordinator, "modelFanPct", "Model Fan", unit_of_measurement="%"),
        CrealitySensor(coordinator, "auxiliaryFanPct", "Auxiliary Fan", unit_of_measurement="%"),
        CrealitySensor(coordinator, "caseFanPct", "Case Fan", unit_of_measurement="%"),
        # Add any additional sensors you need here
    ]
    async_add_entities(sensors)

class CrealitySensor(CoordinatorEntity, Entity):
    """Defines a single Creality sensor."""

    def __init__(self, coordinator, data_key, name_suffix, unit_of_measurement=None):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.data_key = data_key
        self._attr_name = f"Creality {name_suffix}"
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
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self.data_key, "Unknown")

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
            "model": "CR-10 SE",  # Update with your model, have not found a way to get this information
        }

class CrealityTimeLeftSensor(CrealitySensor):
    """Specialized sensor class for handling 'Time Left' data."""

    @property
    def state(self):
        """Return the state of the sensor, converting time to HH:MM:SS format."""
        time_left = int(self.coordinator.data.get(self.data_key, 0))
        return str(timedelta(seconds=time_left))