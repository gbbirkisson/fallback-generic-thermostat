"""Adds support for fallback generic thermostat units."""
from __future__ import annotations

import datetime
import logging
from collections.abc import Mapping
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.climate import PLATFORM_SCHEMA, HVACMode
from homeassistant.components.generic_thermostat.climate import (
    CONF_AC_MODE,
    CONF_COLD_TOLERANCE,
    CONF_HEATER,
    CONF_HOT_TOLERANCE,
    CONF_INITIAL_HVAC_MODE,
    CONF_KEEP_ALIVE,
    CONF_MAX_TEMP,
    CONF_MIN_DUR,
    CONF_MIN_TEMP,
    CONF_PRECISION,
    CONF_PRESETS,
    CONF_SENSOR,
    CONF_TARGET_TEMP,
    CONF_TEMP_STEP,
    DEFAULT_TOLERANCE,
    GenericThermostat,
)
from homeassistant.const import (
    CONF_NAME,
    CONF_UNIQUE_ID,
    PRECISION_HALVES,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConditionError
from homeassistant.helpers import condition
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType, EventType
from typing_extensions import override

from . import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Fallback Generic Thermostat"
CONF_FALLBACK_ON_RATIO = "fallback_on_ratio"
CONF_FALLBACK_INTERVAL = "fallback_interval"
CONF_FALLBACK_FORCE_SWITCH = "fallback_force_switch"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HEATER): cv.entity_id,
        vol.Required(CONF_SENSOR): cv.entity_id,
        vol.Optional(CONF_AC_MODE): cv.boolean,
        vol.Optional(CONF_MAX_TEMP): vol.Coerce(float),
        vol.Optional(CONF_MIN_DUR): cv.positive_time_period,
        vol.Optional(CONF_MIN_TEMP): vol.Coerce(float),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_COLD_TOLERANCE, default=DEFAULT_TOLERANCE): vol.Coerce(float),
        vol.Optional(CONF_HOT_TOLERANCE, default=DEFAULT_TOLERANCE): vol.Coerce(float),
        vol.Optional(CONF_TARGET_TEMP): vol.Coerce(float),
        vol.Optional(CONF_KEEP_ALIVE): cv.positive_time_period,
        vol.Optional(CONF_INITIAL_HVAC_MODE): vol.In(
            [HVACMode.COOL, HVACMode.HEAT, HVACMode.OFF]
        ),
        vol.Optional(CONF_PRECISION): vol.In(
            [PRECISION_TENTHS, PRECISION_HALVES, PRECISION_WHOLE]
        ),
        vol.Optional(CONF_TEMP_STEP): vol.In(
            [PRECISION_TENTHS, PRECISION_HALVES, PRECISION_WHOLE]
        ),
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_FALLBACK_ON_RATIO): vol.Coerce(float),
        vol.Optional(CONF_FALLBACK_INTERVAL): cv.positive_time_period,
        vol.Optional(CONF_FALLBACK_FORCE_SWITCH): cv.entity_id,
    }
).extend({vol.Optional(v): vol.Coerce(float) for (k, v) in CONF_PRESETS.items()})


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the fallback generic thermostat platform."""

    await async_setup_reload_service(hass, DOMAIN, PLATFORMS)

    name = config.get(CONF_NAME)
    heater_entity_id = config.get(CONF_HEATER)
    sensor_entity_id = config.get(CONF_SENSOR)
    min_temp = config.get(CONF_MIN_TEMP)
    max_temp = config.get(CONF_MAX_TEMP)
    target_temp = config.get(CONF_TARGET_TEMP)
    keep_alive = config.get(CONF_KEEP_ALIVE)
    ac_mode = config.get(CONF_AC_MODE)
    min_cycle_duration = config.get(CONF_MIN_DUR)
    cold_tolerance = config.get(CONF_COLD_TOLERANCE)
    hot_tolerance = config.get(CONF_HOT_TOLERANCE)
    initial_hvac_mode = config.get(CONF_INITIAL_HVAC_MODE)
    presets = {
        key: config[value] for key, value in CONF_PRESETS.items() if value in config
    }
    precision = config.get(CONF_PRECISION)
    target_temperature_step = config.get(CONF_TEMP_STEP)
    unit = hass.config.units.temperature_unit
    unique_id = config.get(CONF_UNIQUE_ID)
    fallback_on_ratio = config.get(CONF_FALLBACK_ON_RATIO)
    fallback_interval = config.get(CONF_FALLBACK_INTERVAL) or datetime.timedelta(
        minutes=60
    )
    fallback_force_switch_entity_id = config.get(CONF_FALLBACK_FORCE_SWITCH)

    async_add_entities(
        [
            FallbackGenericThermostat(
                name,
                heater_entity_id,
                sensor_entity_id,
                min_temp,
                max_temp,
                target_temp,
                ac_mode,
                min_cycle_duration,
                cold_tolerance,
                hot_tolerance,
                keep_alive,
                initial_hvac_mode,
                presets,
                precision,
                target_temperature_step,
                unit,
                unique_id,
                fallback_on_ratio,
                fallback_interval,
                fallback_force_switch_entity_id,
            )
        ]
    )


class FallbackGenericThermostat(GenericThermostat):
    def __init__(
        self,
        name,
        heater_entity_id,
        sensor_entity_id,
        min_temp,
        max_temp,
        target_temp,
        ac_mode,
        min_cycle_duration,
        cold_tolerance,
        hot_tolerance,
        keep_alive,
        initial_hvac_mode,
        presets,
        precision,
        target_temperature_step,
        unit,
        unique_id,
        fallback_on_ratio,
        fallback_interval,
        fallback_force_switch_entity_id,
    ):
        """Initialize the thermostat."""
        super().__init__(
            name,
            heater_entity_id,
            sensor_entity_id,
            min_temp,
            max_temp,
            target_temp,
            ac_mode,
            min_cycle_duration,
            cold_tolerance,
            hot_tolerance,
            keep_alive,
            initial_hvac_mode,
            presets,
            precision,
            target_temperature_step,
            unit,
            unique_id,
        )

        self._fallback_on_duration = None
        self._fallback_off_duration = None
        self._fallback_interval = None
        self._fallback_force_switch_entity_id = None
        self._sensor_available = True
        self._fallback_forced = False
        self._static_attributes = {}

        if not fallback_on_ratio:
            return

        if not (0 <= fallback_on_ratio or fallback_on_ratio <= 1):
            _LOGGER.warning(
                "Value for fallback_on_ratio should be between 0 and 1 but is %s",
                fallback_on_ratio,
            )
            return

        self._fallback_on_duration = datetime.timedelta(
            seconds=(fallback_interval.total_seconds() * fallback_on_ratio)
        )
        self._fallback_off_duration = datetime.timedelta(
            seconds=(fallback_interval.total_seconds() * (1 - fallback_on_ratio))
        )
        self._fallback_interval = fallback_interval / 100
        self._fallback_force_switch_entity_id = fallback_force_switch_entity_id
        _LOGGER.info(
            (
                "Fallback mode configured. It will run '%s' ON for %s "
                "and OFF for %s in case '%s' becomes unavailable"
            ),
            self.heater_entity_id,
            self._fallback_on_duration,
            self._fallback_off_duration,
            self.sensor_entity_id,
        )
        self._static_attributes = {
            "fallback_on_duration": str(self._fallback_on_duration),
            "fallback_off_duration": str(self._fallback_off_duration),
            "fallback_interval": str(self._fallback_interval),
        }

    @override
    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        if self._fallback_interval:
            self.async_on_remove(
                async_track_time_interval(
                    self.hass, self._async_control_fallback, self._fallback_interval
                )
            )

            if self._fallback_force_switch_entity_id:
                self.async_on_remove(
                    async_track_state_change_event(
                        self.hass,
                        [self._fallback_force_switch_entity_id],
                        self._async_override_changed,
                    )
                )

    @override
    async def _async_control_heating(self, time=None, force=False) -> None:
        """Check if we need to turn heating on or off if fallback mode is not on"""
        if not self._is_fallback_mode_active:
            await super()._async_control_heating(time=time, force=force)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        self._static_attributes.update(
            {
                "fallback_mode": STATE_ON
                if self._is_fallback_mode_active
                else STATE_OFF,
                "fallback_forced": STATE_ON if self._fallback_forced else STATE_OFF,
            }
        )
        return self._static_attributes

    @override
    async def _async_sensor_changed(
        self, event: EventType[EventStateChangedData]
    ) -> None:
        """Handle temperature changes."""
        new_state = event.data["new_state"]
        if new_state is not None and new_state.state not in (
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        ):
            self._sensor_available = True
            _LOGGER.info(
                "Sensor '%s' has become available, exiting fallback mode!",
                self.sensor_entity_id,
            )
        else:
            self._sensor_available = False
            _LOGGER.warning(
                "Sensor '%s' has become unavailable, entering fallback mode!",
                self.sensor_entity_id,
            )
        if self._is_fallback_mode_active:
            await self._async_control_fallback()
            self.async_write_ha_state()
        else:
            await super()._async_sensor_changed(event)

    async def _async_control_fallback(self, time=None) -> None:
        """Turn heating on or off depending heater state"""
        if self._is_fallback_mode_active:
            async with self._temp_lock:
                device_active = self._is_device_active
                if device_active:
                    current_state = STATE_ON
                    for_how_long = self._fallback_on_duration
                else:
                    current_state = HVACMode.OFF
                    for_how_long = self._fallback_off_duration
                try:
                    long_enough = condition.state(
                        self.hass,
                        self.heater_entity_id,
                        current_state,
                        for_how_long,
                    )
                except ConditionError:
                    long_enough = False

                if long_enough:
                    if device_active:
                        _LOGGER.info(
                            "Climate '%s' running in fallback mode, turning off '%s'",
                            self.name,
                            self.heater_entity_id,
                        )
                        await self._async_heater_turn_off()
                    else:
                        _LOGGER.info(
                            "Climate '%s' running in fallback mode, turning on '%s'",
                            self.name,
                            self.heater_entity_id,
                        )
                        await self._async_heater_turn_on()

    async def _async_override_changed(
        self, event: EventType[EventStateChangedData]
    ) -> None:
        """User has enabled fallback override"""
        new_state = event.data["new_state"]

        if new_state is not None and new_state.state == STATE_ON:
            self._fallback_forced = True
            _LOGGER.info(
                "Fallback override enabled!",
            )
        else:
            self._fallback_forced = False
            _LOGGER.info(
                "Fallback override disabled!",
            )
        self.async_write_ha_state()

    @property
    def _is_fallback_mode_active(self) -> bool:
        """If climate should run in fallback mode."""
        return self._fallback_forced or not self._sensor_available
