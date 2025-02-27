"""Support for Alpha2 room control unit via Alpha2 base."""
import logging

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import (
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import Alpha2BaseCoordinator
from .const import DOMAIN, PRESET_AUTO, PRESET_DAY, PRESET_NIGHT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add Alpha2Climate entities from a config_entry."""

    coordinator: Alpha2BaseCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        Alpha2Climate(coordinator, heat_area_id) for heat_area_id in coordinator.data
    )


# https://developers.home-assistant.io/docs/core/entity/climate/
class Alpha2Climate(CoordinatorEntity[Alpha2BaseCoordinator], ClimateEntity):
    """Alpha2 ClimateEntity."""

    target_temperature_step = 0.2

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_hvac_modes = [HVAC_MODE_HEAT, HVAC_MODE_COOL]
    _attr_temperature_unit = TEMP_CELSIUS
    _attr_preset_modes = [PRESET_AUTO, PRESET_DAY, PRESET_NIGHT]

    def __init__(self, coordinator: Alpha2BaseCoordinator, heat_area_id: str) -> None:
        """Initialize Alpha2 ClimateEntity."""
        super().__init__(coordinator)
        self.heat_area_id = heat_area_id

    @property
    def name(self) -> str:
        """Return the name of the climate device."""
        return self.coordinator.data[self.heat_area_id]["HEATAREA_NAME"]

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return float(self.coordinator.data[self.heat_area_id].get("T_TARGET_MIN", 0.0))

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return float(self.coordinator.data[self.heat_area_id].get("T_TARGET_MAX", 30.0))

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        return float(self.coordinator.data[self.heat_area_id].get("T_ACTUAL", 0.0))

    @property
    def hvac_mode(self) -> str:
        """Return current hvac mode."""
        if self.coordinator.get_cooling():
            return HVAC_MODE_COOL
        return HVAC_MODE_HEAT

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target hvac mode."""
        await self.coordinator.async_set_cooling(hvac_mode == HVAC_MODE_COOL)

    @property
    def hvac_action(self) -> str:
        """Return the current running hvac operation."""
        if not self.coordinator.data[self.heat_area_id]["_HEATCTRL_STATE"]:
            return CURRENT_HVAC_IDLE
        if self.coordinator.get_cooling():
            return CURRENT_HVAC_COOL
        return CURRENT_HVAC_HEAT

    @property
    def target_temperature(self) -> float:
        """Return the temperature we try to reach."""
        return float(self.coordinator.data[self.heat_area_id].get("T_TARGET", 0.0))

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperatures."""
        if (target_temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        await self.coordinator.async_set_target_temperature(
            self.heat_area_id, target_temperature
        )

    @property
    def preset_mode(self) -> str:
        """Return the current preset mode."""
        if self.coordinator.data[self.heat_area_id]["HEATAREA_MODE"] == 1:
            return PRESET_DAY
        if self.coordinator.data[self.heat_area_id]["HEATAREA_MODE"] == 2:
            return PRESET_NIGHT
        return PRESET_AUTO

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new operation mode."""
        heat_area_mode = 0
        if preset_mode == PRESET_DAY:
            heat_area_mode = 1
        elif preset_mode == PRESET_NIGHT:
            heat_area_mode = 2

        await self.coordinator.async_set_heat_area_mode(
            self.heat_area_id, heat_area_mode
        )
