"""
Contains functionality to use a X10 dimmer over Mochad.

For more details about this platform, please refer to the documentation at
https://home.assistant.io/components/light.mochad/
"""

import logging

import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, Light, PLATFORM_SCHEMA)
from homeassistant.components import mochad
from homeassistant.const import (CONF_NAME, CONF_PLATFORM, CONF_DEVICES,
                                 CONF_ADDRESS)
from homeassistant.helpers import config_validation as cv

DEPENDENCIES = ['mochad']
_LOGGER = logging.getLogger(__name__)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PLATFORM): mochad.DOMAIN,
    CONF_DEVICES: [{
        vol.Optional(CONF_NAME): cv.string,
        vol.Required(CONF_ADDRESS): cv.x10_address,
        vol.Optional(mochad.CONF_COMM_TYPE): cv.string,
    }]
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up X10 dimmers over a mochad controller."""
    devs = config.get(CONF_DEVICES)
    add_devices([MochadLight(
        hass, mochad.CONTROLLER.ctrl, dev) for dev in devs])
    return True


class MochadLight(Light):
    """Representation of a X10 dimmer over Mochad."""

    def __init__(self, hass, ctrl, dev):
        """Initialize a Mochad Light Device."""
        from pymochad import device

        self._controller = ctrl
        self._address = dev[CONF_ADDRESS]
        self._name = dev.get(CONF_NAME,
                             'x10_light_dev_{}'.format(self._address))
        self._comm_type = dev.get(mochad.CONF_COMM_TYPE, 'pl')
        self.device = device.Device(ctrl, self._address,
                                    comm_type=self._comm_type)
        self._brightness = 0
        self._state = self._get_device_status()

    @property
    def brightness(self):
        """Return the birghtness of this light between 0..255."""
        return self._brightness

    def _get_device_status(self):
        """Get the status of the light from mochad."""
        with mochad.REQ_LOCK:
            status = self.device.get_status().rstrip()
        return status == 'on'

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._state

    @property
    def supported_features(self):
        """Return supported features."""
        return SUPPORT_BRIGHTNESS

    @property
    def assumed_state(self):
        """X10 devices are normally 1-way so we have to assume the state."""
        return True

    def turn_on(self, **kwargs):
        """Send the command to turn the light on."""
        self._brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        with mochad.REQ_LOCK:
            self.device.send_cmd("xdim {}".format(self._brightness))
            self._controller.read_data()
        self._state = True

    def turn_off(self, **kwargs):
        """Send the command to turn the light on."""
        with mochad.REQ_LOCK:
            self.device.send_cmd('off')
            self._controller.read_data()
        self._state = False
