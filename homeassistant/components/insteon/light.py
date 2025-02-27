"""Support for Insteon lights via PowerLinc Modem."""
from pyinsteon.extended_property import ON_LEVEL

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    DOMAIN as LIGHT_DOMAIN,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import SIGNAL_ADD_ENTITIES
from .insteon_entity import InsteonEntity
from .utils import async_add_insteon_entities

MAX_BRIGHTNESS = 255


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Insteon lights from a config entry."""

    @callback
    def async_add_insteon_light_entities(discovery_info=None):
        """Add the Insteon entities for the platform."""
        async_add_insteon_entities(
            hass, LIGHT_DOMAIN, InsteonDimmerEntity, async_add_entities, discovery_info
        )

    signal = f"{SIGNAL_ADD_ENTITIES}_{LIGHT_DOMAIN}"
    async_dispatcher_connect(hass, signal, async_add_insteon_light_entities)
    async_add_insteon_light_entities()


class InsteonDimmerEntity(InsteonEntity, LightEntity):
    """A Class for an Insteon light entity."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        return self._insteon_device_group.value

    @property
    def is_on(self):
        """Return the boolean response if the node is on."""
        return bool(self.brightness)

    async def async_turn_on(self, **kwargs):
        """Turn light on."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = int(kwargs[ATTR_BRIGHTNESS])
        else:
            brightness = self.get_device_property(ON_LEVEL)
        if brightness is not None:
            await self._insteon_device.async_on(
                on_level=brightness, group=self._insteon_device_group.group
            )
        else:
            await self._insteon_device.async_on(group=self._insteon_device_group.group)

    async def async_turn_off(self, **kwargs):
        """Turn light off."""
        await self._insteon_device.async_off(self._insteon_device_group.group)
