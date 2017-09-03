"""
Device Trackers for Husqvarna Automowers.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.automower/
"""

from homeassistant.components.automower import DOMAIN as AUTOMOWER_DOMAIN

DEPENDENCIES = ['automower']

def setup_scanner(hass, config, see, discovery_info=None):
    """Set up the Husqvarna Automower tracker."""
    for device in hass.data[AUTOMOWER_DOMAIN]['devices']:
        device.set_see(see)
    return True
