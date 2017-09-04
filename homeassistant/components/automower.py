"""
Platform for Husqvarna Automowers.

For more details about this component, please refer to the documentation
https://home-assistant.io/components/automower/
"""

import copy
import logging
import voluptuous as vol

from datetime import datetime
from homeassistant.const import CONF_ICON, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity
from homeassistant.util import slugify

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['pyhusmow==0.1']
DOMAIN = 'automower'
DEFAULT_ICON = 'mdi:robot'
VENDOR = 'Husqvarna'

# Add more states
STATE_ICONS = {
    'ERROR': 'mdi:alert',
    'OK_CHARGING': 'mdi:power-plug',
    'PARKED_TIMER': 'mdi:timetable'
}

ERROR_MESSAGES = {
    1: 'Outside working area'
}

# TODO: Add more models
MODELS = {
    'H': 'Automower 450X'
}

IGNORED_API_STATE_ATTRIBUTES = [
    'cachedSettingsUUID',
    'lastLocations',
    'valueFound'
]

AUTOMOWER_COMPONENTS = [
    'sensor', 'device_tracker'
]

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=30):
            vol.All(cv.positive_int, vol.Clamp(min=30)),
    }),
}, extra=vol.ALLOW_EXTRA)

def setup(hass, base_config):
    """Establish connection to Husqvarna Automower API."""
    from pyhusmow import API as HUSMOW_API

    config = base_config.get(DOMAIN)

    if hass.data.get(DOMAIN) is None:
        hass.data[DOMAIN] = { 'devices': [] }

    api = HUSMOW_API()
    api.login(config.get(CONF_USERNAME), config.get(CONF_PASSWORD))

    robots = api.list_robots()

    if not robots:
        return False

    for robot in robots:
        hass.data[DOMAIN]['devices'].append(AutomowerDevice(robot, api))

    for component in AUTOMOWER_COMPONENTS:
        discovery.load_platform(hass, component, DOMAIN, {}, base_config)

    return True


class AutomowerDevice(Entity):
    """Representation of an Automower device."""

    def __init__(self, meta, api):
        """Initialisation of the Automower device."""
        _LOGGER.debug("Initializing Automower device: %s", meta['name'])
        self._id = meta['id']
        self._name = meta['name']
        self._model = meta['model']
        self._state = None
        self._see = None

        # select robot in api
        self._api = copy.copy(api)
        self._api.select_robot(self._id)

    @property
    def id(self):
        """Return the id of the Automower."""
        return self._id

    @property
    def dev_id(self):
        return slugify("{0}_{1}_{2}".format(DOMAIN, self._model, self._id))

    @property
    def name(self):
        """Return the name of the Automower."""
        return self._name

    @property
    def model(self):
        """Return the model of the Automower."""
        return MODELS.get(self._model,self._model)

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return STATE_ICONS.get(self.state, DEFAULT_ICON)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state['mowerStatus']

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""

        attributes = self._state

        # make some attributes more human readable
        attributes['lastErrorMessage'] = ERROR_MESSAGES.get(attributes['lastErrorCode'])
        attributes['storedTimestamp'] = attributes['storedTimestamp'] / 1000.0
        for key in ['lastErrorCodeTimestamp', 'nextStartTimestamp', 'storedTimestamp']:
            if key in attributes:
                attributes[key] = datetime.utcfromtimestamp(attributes[key])

        # remove attributes that are exposed via properties or irrelevant
        return { k: v for k, v in attributes.items() if not k in IGNORED_API_STATE_ATTRIBUTES }

    @property
    def battery(self):
        return self._state['batteryPercent']

    @property
    def lat(self):
        return self._state['lastLocations'][0]['latitude']

    @property
    def lon(self):
        return self._state['lastLocations'][0]['longitude']

    def set_see(self, see):
        self._see = see

    def update(self):
        """Update the state from the sensor."""
        _LOGGER.debug("Updating sensor: %s", self._name)
        self._state = self._api.status()
        if self._see is not None:
            self.update_see()

    def update_see(self):
        """Update the device tracker."""
        _LOGGER.debug("Updating device tracker: %s", self._name)
        self._see(
            dev_id=self.dev_id,
            host_name=self.name,
            battery=self.battery,
            gps=(self.lat, self.lon),
            attributes={
                'status': self.state,
                'id': self.dev_id,
                'name': self.name,
                CONF_ICON: self.icon,
                'vendor': VENDOR,
                'model': self.model})
