"""
Sensors for Husqvarna Automowers.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.automower/
"""
import logging
from datetime import timedelta

from homeassistant.const import ATTR_BATTERY_LEVEL, CONF_STATE, CONF_ICON
from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.components.automower import DOMAIN as AUTOMOWER_DOMAIN, ICON as AUTOMOWER_ICON, VENDOR as AUTOMOWER_VENDOR, AutomowerDevice
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import track_utc_time_change
from homeassistant.util import slugify

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['automower']

SCAN_INTERVAL = timedelta(seconds=30)

def setup_scanner(hass, config, see, discovery_info=None):
    """Set up the Husqvarna Automower tracker."""
    AutomowerDeviceTracker(
        hass, config, see,
        hass.data[AUTOMOWER_DOMAIN]['devices'])
    return True


class AutomowerDeviceTracker(object):
    """A class representing the Automower device tracker."""

    def __init__(self, hass, config, see, devices):
        """Initialize the Automower device scanner."""
        _LOGGER.debug("Initializing Automower device scanner.")
        self.hass = hass
        self.see = see
        self.devices = devices
        self._update_info()

        track_utc_time_change(
            self.hass, self._update_info, second=range(0, 60, 30))

    def _update_info(self, now=None):
        """Update the device info."""
        for device in self.devices:
            _LOGGER.debug("Updating Automower device position: %s", device['meta']['name'])
            status = device['api'].status()
            device_id = slugify("automower_{0}_{1}".format(
                device['meta']['model'],
                device['meta']['id']))
            last_location = status['lastLocations'][0]
            self.see(
                dev_id=device_id,
                host_name=device['meta']['name'],
                battery=status['batteryPercent'],
                gps=(
                    last_location['latitude'],
                    last_location['longitude']),
                attributes={
                    'id': device_id,
                    'name': device['meta']['name'],
                    CONF_ICON: AUTOMOWER_ICON,
                    'vendor': AUTOMOWER_VENDOR,
                    'model': device['meta']['model']})
