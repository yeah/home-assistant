"""
Sensors for Husqvarna Automowers.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.automower/
"""
import logging
from datetime import timedelta

from homeassistant.const import ATTR_BATTERY_LEVEL, CONF_STATE
from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.components.automower import DOMAIN as AUTOMOWER_DOMAIN, AutomowerDevice
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['automower']

SCAN_INTERVAL = timedelta(seconds=30)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Husqvarna Automower sensor platform."""
    devices = []

    for device in hass.data[AUTOMOWER_DOMAIN]['devices']:
        devices.append(
            AutomowerSensor(
                device['meta']['id'],
                device['meta']['name'],
                device['meta']['model'],
                device['api']
            )
        )

    add_devices(devices, True)


class AutomowerSensor(AutomowerDevice, Entity):
    """Representation of Automower sensors."""

    def __init__(self, id, name, model, api, sensor_type=None):
        """Initialisation of the sensor."""
        super().__init__(id, name, model, api)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state['mowerStatus']

    def update(self):
        """Update the state from the sensor."""
        _LOGGER.debug("Updating sensor: %s", self._name)
        self._state = self._api.status()
