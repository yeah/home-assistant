"""
Platform for Husqvarna Automowers.

For more details about this component, please refer to the documentation
https://home-assistant.io/components/automower/
"""

import copy
import logging
import voluptuous as vol

from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['pyhusmow==0.1']

DOMAIN = 'automower'

AUTOMOWER_API_CLIENT_HANDLE = 'automower'

ICON = 'mdi:robot'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=30):
            vol.All(cv.positive_int, vol.Clamp(min=30)),

    }),
}, extra=vol.ALLOW_EXTRA)

AUTOMOWER_COMPONENTS = [
    'sensor'
]


def setup(hass, base_config):
    """Establish connection to Husqvarna Automower API."""
    from pyhusmow import API

    config = base_config.get(DOMAIN)

    if hass.data.get(DOMAIN) is None:
        hass.data[DOMAIN] = { 'devices': [] }

    api = API()
    api.login(config.get(CONF_USERNAME), config.get(CONF_PASSWORD))

    robots = api.list_robots()

    if not robots:
        return False

    for robot in robots:
        device_api = copy.copy(api)
        device_api.select_robot(robot['id'])
        hass.data[DOMAIN]['devices'].append({'meta': robot, 'api': device_api})

    for component in AUTOMOWER_COMPONENTS:
        discovery.load_platform(hass, component, DOMAIN, {}, base_config)

    return True


class AutomowerDevice(Entity):
    """Representation of an Automower device."""

    def __init__(self, id, name, model, api):
        """Initialisation of the Automower device."""
        self._id = id
        self._name = name
        self._model = model
        self._state = None
        self._api = api

    @property
    def id(self):
        """Return the id of the Automower."""
        return self._id

    @property
    def name(self):
        """Return the name of the Automower."""
        return self._name

    @property
    def model(self):
        """Return the model of the Automower."""
        return self._model

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return ICON

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return self._state

    def update(self):
        """Update the state from the sensor."""
        _LOGGER.debug("Updating sensor: %s", self._name)
        self._state = self._api.status()
