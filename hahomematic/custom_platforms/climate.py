"""Code to create the required entities for thermostat devices."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from hahomematic.backport import StrEnum
from hahomematic.const import HmPlatform
from hahomematic.custom_platforms.entity_definition import (
    FIELD_ACTIVE_PROFILE,
    FIELD_AUTO_MODE,
    FIELD_BOOST_MODE,
    FIELD_COMFORT_MODE,
    FIELD_CONTROL_MODE,
    FIELD_HEATING_COOLING,
    FIELD_HUMIDITY,
    FIELD_LEVEL,
    FIELD_LOWERING_MODE,
    FIELD_MANU_MODE,
    FIELD_PARTY_MODE,
    FIELD_SET_POINT_MODE,
    FIELD_SETPOINT,
    FIELD_STATE,
    FIELD_TEMPERATURE,
    FIELD_TEMPERATURE_MAXIMUM,
    FIELD_TEMPERATURE_MINIMUM,
    FIELD_VALVE_STATE,
    EntityDefinition,
    make_custom_entity,
)
from hahomematic.decorators import value_property
import hahomematic.device as hmd
import hahomematic.entity as hme
from hahomematic.entity import CustomEntity
from hahomematic.generic_platforms.action import HmAction
from hahomematic.generic_platforms.binary_sensor import HmBinarySensor
from hahomematic.generic_platforms.number import HmFloat, HmInteger
from hahomematic.generic_platforms.select import HmSelect
from hahomematic.generic_platforms.sensor import HmSensor
from hahomematic.generic_platforms.switch import HmSwitch

_LOGGER = logging.getLogger(__name__)

# HA constants
HM_MODE_AUTO = "AUTO-MODE"  # 0
HM_MODE_MANU = "MANU-MODE"  # 1
HM_MODE_AWAY = "PARTY-MODE"  # 2
HM_MODE_BOOST = "BOOST-MODE"  # 3

HM_OFF_TEMPERATURE = 4.5

HMIP_MODE_AUTO = 0
HMIP_MODE_MANU = 1
HMIP_MODE_AWAY = 2

PARTY_INIT_DATE = "2000_01_01 00:00"
PARTY_DATE_FORMAT = "%Y_%m_%d %H:%M"

HM_PRESET_MODE_PREFIX = "week_program_"
TEMP_CELSIUS = "°C"


class HmHvacAction(StrEnum):
    """Enum with the hvac actions."""

    COOL = "cooling"
    HEAT = "heating"
    IDLE = "idle"
    OFF = "off"


class HmHvacMode(StrEnum):
    """Enum with the hvac modes."""

    OFF = "off"
    HEAT = "heat"
    AUTO = "auto"
    COOL = "cool"


class HmPresetMode(StrEnum):
    """Enum with preset modes."""

    NONE = "none"
    AWAY = "away"
    BOOST = "boost"
    COMFORT = "comfort"
    ECO = "eco"
    WEEK_PROGRAM_1 = "week_program_1"
    WEEK_PROGRAM_2 = "week_program_2"
    WEEK_PROGRAM_3 = "week_program_3"
    WEEK_PROGRAM_4 = "week_program_4"
    WEEK_PROGRAM_5 = "week_program_5"
    WEEK_PROGRAM_6 = "week_program_6"


class BaseClimateEntity(CustomEntity):
    """Base HomeMatic climate entity."""

    _attr_platform = HmPlatform.CLIMATE

    def _init_entity_fields(self) -> None:
        """Init the entity fields."""
        super()._init_entity_fields()
        self._e_humidity: HmSensor = self._get_entity(
            field_name=FIELD_HUMIDITY, entity_type=HmSensor
        )
        self._e_setpoint: HmFloat = self._get_entity(
            field_name=FIELD_SETPOINT, entity_type=HmFloat
        )
        self._e_temperature: HmSensor = self._get_entity(
            field_name=FIELD_TEMPERATURE, entity_type=HmSensor
        )
        self._e_temperature_maximum: HmSensor = self._get_entity(
            field_name=FIELD_TEMPERATURE_MAXIMUM, entity_type=HmSensor
        )
        self._e_temperature_minimum: HmSensor = self._get_entity(
            field_name=FIELD_TEMPERATURE_MINIMUM, entity_type=HmSensor
        )

    @value_property
    def temperature_unit(self) -> str:
        """Return temperature unit."""
        return TEMP_CELSIUS

    @value_property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        if self._e_temperature_minimum and self._e_temperature_minimum.value:
            min_temp = float(self._e_temperature_minimum.value)
        else:
            min_temp = self._e_setpoint.min

        if min_temp == HM_OFF_TEMPERATURE:
            return min_temp + 0.5
        return min_temp

    @value_property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        if self._e_temperature_maximum and self._e_temperature_maximum.value:
            return float(self._e_temperature_maximum.value)
        return self._e_setpoint.max

    @value_property
    def current_humidity(self) -> int | None:
        """Return the current humidity."""
        return self._e_humidity.value

    @value_property
    def current_temperature(self) -> float | None:
        """Return current temperature."""
        return self._e_temperature.value

    @value_property
    def target_temperature(self) -> float | None:
        """Return target temperature."""
        return self._e_setpoint.value

    @value_property
    def target_temperature_step(self) -> float:
        """Return the supported step of target temperature."""
        return 0.5

    @value_property
    def preset_mode(self) -> HmPresetMode:
        """Return the current preset mode."""
        return HmPresetMode.NONE

    @value_property
    def preset_modes(self) -> list[HmPresetMode]:
        """Return available preset modes."""
        return [HmPresetMode.NONE]

    @value_property
    def hvac_action(self) -> HmHvacAction | None:
        """Return the hvac action"""
        return None

    @value_property
    def hvac_mode(self) -> HmHvacMode:
        """Return hvac operation mode."""
        return HmHvacMode.HEAT

    @value_property
    def hvac_modes(self) -> list[HmHvacMode]:
        """Return the list of available hvac operation modes."""
        return [HmHvacMode.HEAT]

    @value_property
    def supports_preset(self) -> bool:
        """Flag if climate supports preset."""
        return False

    @property
    def _min_or_target_temperature(self) -> float:
        """Return the min or target temperature"""
        temperature: float = self.target_temperature or self.min_temp
        if temperature < self.min_temp:
            temperature = self.min_temp
        return temperature

    async def set_temperature(
        self, temperature: float, do_validate: bool = True
    ) -> None:
        """Set new target temperature."""
        await self._e_setpoint.send_value(value=temperature, do_validate=do_validate)

    async def set_hvac_mode(self, hvac_mode: HmHvacMode) -> None:
        """Set new target hvac mode."""
        return None

    async def set_preset_mode(self, preset_mode: HmPresetMode) -> None:
        """Set new preset mode."""
        return None

    async def enable_away_mode_by_calendar(
        self, start: datetime, end: datetime, away_temperature: float
    ) -> None:
        """Enable the away mode by calendar on thermostat."""
        return None

    async def enable_away_mode_by_duration(
        self, hours: int, away_temperature: float
    ) -> None:
        """Enable the away mode by duration on thermostat."""
        return None

    async def disable_away_mode(self) -> None:
        """Disable the away mode on thermostat."""
        return None


class CeSimpleRfThermostat(BaseClimateEntity):
    """Simple classic HomeMatic thermostat HM-CC-TC."""


class CeRfThermostat(BaseClimateEntity):
    """Classic HomeMatic thermostat like HM-CC-RT-DN."""

    def _init_entity_fields(self) -> None:
        """Init the entity fields."""
        super()._init_entity_fields()
        self._e_boost_mode: HmSwitch = self._get_entity(
            field_name=FIELD_BOOST_MODE, entity_type=HmSwitch
        )
        self._e_auto_mode: HmAction = self._get_entity(
            field_name=FIELD_AUTO_MODE, entity_type=HmAction
        )
        self._e_manu_mode: HmAction = self._get_entity(
            field_name=FIELD_MANU_MODE, entity_type=HmAction
        )
        self._e_comfort_mode: HmAction = self._get_entity(
            field_name=FIELD_COMFORT_MODE, entity_type=HmAction
        )
        self._e_lowering_mode: HmAction = self._get_entity(
            field_name=FIELD_LOWERING_MODE, entity_type=HmAction
        )
        self._e_control_mode: HmSensor = self._get_entity(
            field_name=FIELD_CONTROL_MODE, entity_type=HmSensor
        )
        self._e_valve_state: HmSensor = self._get_entity(
            field_name=FIELD_VALVE_STATE, entity_type=HmSensor
        )

    @value_property
    def hvac_action(self) -> HmHvacAction | None:
        """Return the hvac action"""
        if self._e_valve_state.value is None:
            return None
        if self.hvac_mode == HmHvacMode.OFF:
            return HmHvacAction.OFF
        if self._e_valve_state.value and self._e_valve_state.value > 0:
            return HmHvacAction.HEAT
        return HmHvacAction.IDLE

    @value_property
    def hvac_mode(self) -> HmHvacMode:
        """Return hvac operation mode."""
        if self.target_temperature and self.target_temperature <= HM_OFF_TEMPERATURE:
            return HmHvacMode.OFF
        if self._e_control_mode.value == HM_MODE_MANU:
            return HmHvacMode.HEAT
        return HmHvacMode.AUTO

    @value_property
    def hvac_modes(self) -> list[HmHvacMode]:
        """Return the list of available hvac operation modes."""
        return [HmHvacMode.AUTO, HmHvacMode.HEAT, HmHvacMode.OFF]

    @value_property
    def preset_mode(self) -> HmPresetMode:
        """Return the current preset mode."""
        if self._e_control_mode.value is None:
            return HmPresetMode.NONE
        if self._e_control_mode.value == HM_MODE_BOOST:
            return HmPresetMode.BOOST
        if self._e_control_mode.value == HM_MODE_AWAY:
            return HmPresetMode.AWAY
        return HmPresetMode.NONE

    @value_property
    def preset_modes(self) -> list[HmPresetMode]:
        """Return available preset modes."""
        return [
            HmPresetMode.BOOST,
            HmPresetMode.COMFORT,
            HmPresetMode.ECO,
            HmPresetMode.NONE,
        ]

    @value_property
    def supports_preset(self) -> bool:
        """Flag if climate supports preset."""
        return True

    async def set_hvac_mode(self, hvac_mode: HmHvacMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HmHvacMode.AUTO:
            await self._e_auto_mode.send_value(True)
        elif hvac_mode == HmHvacMode.HEAT:
            await self._e_manu_mode.send_value(self._min_or_target_temperature)
        elif hvac_mode == HmHvacMode.OFF:
            await self._e_manu_mode.send_value(self.target_temperature)
            # Disable validation here to allow setting a value,
            # that is out of the validation range.
            await self.set_temperature(
                temperature=HM_OFF_TEMPERATURE, do_validate=False
            )

    async def set_preset_mode(self, preset_mode: HmPresetMode) -> None:
        """Set new preset mode."""
        if preset_mode == HmPresetMode.BOOST:
            await self._e_boost_mode.send_value(True)
        elif preset_mode == HmPresetMode.COMFORT:
            await self._e_comfort_mode.send_value(True)
        elif preset_mode == HmPresetMode.ECO:
            await self._e_lowering_mode.send_value(True)


class CeIpThermostat(BaseClimateEntity):
    """HomematicIP thermostat like HmIP-eTRV-B."""

    def _init_entity_fields(self) -> None:
        """Init the entity fields."""
        super()._init_entity_fields()
        self._e_active_profile: HmInteger = self._get_entity(
            field_name=FIELD_ACTIVE_PROFILE, entity_type=HmInteger
        )
        self._e_boost_mode: HmSwitch = self._get_entity(
            field_name=FIELD_BOOST_MODE, entity_type=HmSwitch
        )
        self._e_control_mode: HmAction = self._get_entity(
            field_name=FIELD_CONTROL_MODE, entity_type=HmAction
        )
        self._e_heating_mode: HmSelect = self._get_entity(
            field_name=FIELD_HEATING_COOLING, entity_type=HmSelect
        )
        self._e_party_mode: HmBinarySensor = self._get_entity(
            field_name=FIELD_PARTY_MODE, entity_type=HmBinarySensor
        )
        self._e_set_point_mode: HmInteger = self._get_entity(
            field_name=FIELD_SET_POINT_MODE, entity_type=HmInteger
        )
        self._e_level: HmSensor = self._get_entity(
            field_name=FIELD_LEVEL, entity_type=HmSensor
        )
        self._e_state: HmBinarySensor = self._get_entity(
            field_name=FIELD_STATE, entity_type=HmBinarySensor
        )

    @property
    def _is_heating_mode(self) -> bool:
        """Return the heating_mode of the device."""
        if self._e_heating_mode.value:
            return str(self._e_heating_mode.value) == "HEATING"
        return True

    @value_property
    def hvac_action(self) -> HmHvacAction | None:
        """Return the hvac action"""
        if self._e_state.value is None and self._e_level.value is None:
            return None
        if self.hvac_mode == HmHvacMode.OFF:
            return HmHvacAction.OFF
        if self._e_state.value is True or (
            self._e_level.value and self._e_level.value > 0.0
        ):
            return HmHvacAction.HEAT if self._is_heating_mode else HmHvacAction.COOL
        return HmHvacAction.IDLE

    @value_property
    def hvac_mode(self) -> HmHvacMode:
        """Return hvac operation mode."""
        if self.target_temperature and self.target_temperature <= HM_OFF_TEMPERATURE:
            return HmHvacMode.OFF
        if self._e_set_point_mode.value == HMIP_MODE_MANU:
            return HmHvacMode.HEAT if self._is_heating_mode else HmHvacMode.COOL
        if self._e_set_point_mode.value == HMIP_MODE_AUTO:
            return HmHvacMode.AUTO
        return HmHvacMode.AUTO

    @value_property
    def hvac_modes(self) -> list[HmHvacMode]:
        """Return the list of available hvac operation modes."""
        return [
            HmHvacMode.AUTO,
            HmHvacMode.HEAT if self._is_heating_mode else HmHvacMode.COOL,
            HmHvacMode.OFF,
        ]

    @value_property
    def preset_mode(self) -> HmPresetMode:
        """Return the current preset mode."""
        if self._e_boost_mode.value:
            return HmPresetMode.BOOST
        if self._e_set_point_mode.value == HMIP_MODE_AWAY:
            return HmPresetMode.AWAY
        if self.hvac_mode == HmHvacMode.AUTO:
            return (
                self._current_profile_name
                if self._current_profile_name
                else HmPresetMode.NONE
            )
        return HmPresetMode.NONE

    @value_property
    def preset_modes(self) -> list[HmPresetMode]:
        """Return available preset modes."""
        presets = [HmPresetMode.BOOST, HmPresetMode.NONE]
        if self.hvac_mode == HmHvacMode.AUTO:
            presets.extend(self._profile_names)
        return presets

    @value_property
    def supports_preset(self) -> bool:
        """Flag if climate supports preset."""
        return True

    async def set_hvac_mode(self, hvac_mode: HmHvacMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HmHvacMode.AUTO:
            await self._e_control_mode.send_value(HMIP_MODE_AUTO)
        elif hvac_mode in (HmHvacMode.HEAT, HmHvacMode.COOL):
            await self._e_control_mode.send_value(HMIP_MODE_MANU)
            await self.set_temperature(temperature=self._min_or_target_temperature)
        elif hvac_mode == HmHvacMode.OFF:
            await self._e_control_mode.send_value(HMIP_MODE_MANU)
            await self.set_temperature(temperature=HM_OFF_TEMPERATURE)
        # if switching hvac_mode then disable boost_mode
        if self._e_boost_mode.value:
            await self.set_preset_mode(HmPresetMode.NONE)

    async def set_preset_mode(self, preset_mode: HmPresetMode) -> None:
        """Set new preset mode."""
        if preset_mode == HmPresetMode.BOOST:
            await self._e_boost_mode.send_value(True)
        elif preset_mode == HmPresetMode.NONE:
            await self._e_boost_mode.send_value(False)
        elif preset_mode in self._profile_names:
            if self.hvac_mode != HmHvacMode.AUTO:
                await self.set_hvac_mode(HmHvacMode.AUTO)
            profile_idx = self._profiles.get(preset_mode)
            await self._e_boost_mode.send_value(False)
            if profile_idx:
                await self._e_active_profile.send_value(profile_idx)

    async def enable_away_mode_by_calendar(
        self, start: datetime, end: datetime, away_temperature: float
    ) -> None:
        """Enable the away mode by calendar on thermostat."""
        await self.put_paramset(
            paramset_key="VALUES",
            value={
                "CONTROL_MODE": HMIP_MODE_AWAY,
                "PARTY_TIME_END": end.strftime(PARTY_DATE_FORMAT),
                "PARTY_TIME_START": start.strftime(PARTY_DATE_FORMAT),
            },
        )
        await self.put_paramset(
            paramset_key="VALUES",
            value={
                "SET_POINT_TEMPERATURE": away_temperature,
            },
        )

    async def enable_away_mode_by_duration(
        self, hours: int, away_temperature: float
    ) -> None:
        """Enable the away mode by duration on thermostat."""
        start = datetime.now() - timedelta(minutes=10)
        end = datetime.now() + timedelta(hours=hours)
        await self.enable_away_mode_by_calendar(
            start=start, end=end, away_temperature=away_temperature
        )

    async def disable_away_mode(self) -> None:
        """Disable the away mode on thermostat."""
        await self.put_paramset(
            paramset_key="VALUES",
            value={
                "CONTROL_MODE": HMIP_MODE_AWAY,
                "PARTY_TIME_START": PARTY_INIT_DATE,
                "PARTY_TIME_END": PARTY_INIT_DATE,
            },
        )

    @property
    def _profile_names(self) -> list[HmPresetMode]:
        """Return a collection of profile names."""
        return list(self._profiles.keys())

    @property
    def _current_profile_name(self) -> HmPresetMode | None:
        """Return a profile index by name."""
        inv_profiles: dict[int, HmPresetMode] = {
            v: k for k, v in self._profiles.items()
        }
        if self._e_active_profile.value:
            return inv_profiles.get(int(self._e_active_profile.value))
        return None

    @property
    def _profiles(self) -> dict[HmPresetMode, int]:
        """Return the profile groups."""
        profiles: dict[HmPresetMode, int] = {}
        if self._e_active_profile.min and self._e_active_profile.max:
            for i in range(self._e_active_profile.min, self._e_active_profile.max + 1):
                profiles[HmPresetMode(f"{HM_PRESET_MODE_PREFIX}{i}")] = i

        return profiles


def make_simple_thermostat(
    device: hmd.HmDevice, group_base_channels: tuple[int, ...]
) -> tuple[hme.BaseEntity, ...]:
    """Creates SimpleRfThermostat entities."""
    return make_custom_entity(
        device=device,
        custom_entity_class=CeSimpleRfThermostat,
        device_enum=EntityDefinition.SIMPLE_RF_THERMOSTAT,
        group_base_channels=group_base_channels,
    )


def make_thermostat(
    device: hmd.HmDevice, group_base_channels: tuple[int, ...]
) -> tuple[hme.BaseEntity, ...]:
    """Creates RfThermostat entities."""
    return make_custom_entity(
        device=device,
        custom_entity_class=CeRfThermostat,
        device_enum=EntityDefinition.RF_THERMOSTAT,
        group_base_channels=group_base_channels,
    )


def make_thermostat_group(
    device: hmd.HmDevice, group_base_channels: tuple[int, ...]
) -> tuple[hme.BaseEntity, ...]:
    """Creates RfThermostat group entities."""
    return make_custom_entity(
        device=device,
        custom_entity_class=CeRfThermostat,
        device_enum=EntityDefinition.RF_THERMOSTAT_GROUP,
        group_base_channels=group_base_channels,
    )


def make_ip_thermostat(
    device: hmd.HmDevice, group_base_channels: tuple[int, ...]
) -> tuple[hme.BaseEntity, ...]:
    """Creates IPThermostat entities."""
    return make_custom_entity(
        device=device,
        custom_entity_class=CeIpThermostat,
        device_enum=EntityDefinition.IP_THERMOSTAT,
        group_base_channels=group_base_channels,
    )


def make_ip_thermostat_group(
    device: hmd.HmDevice, group_base_channels: tuple[int, ...]
) -> tuple[hme.BaseEntity, ...]:
    """Creates IPThermostat group entities."""
    return make_custom_entity(
        device=device,
        custom_entity_class=CeIpThermostat,
        device_enum=EntityDefinition.IP_THERMOSTAT_GROUP,
        group_base_channels=group_base_channels,
    )


# Case for device model is not relevant
DEVICES: dict[str, tuple[Any, tuple[int, ...]]] = {
    "ALPHA-IP-RBG": (make_ip_thermostat, (1,)),
    "BC-RT-TRX-CyG": (make_thermostat, (1,)),
    "BC-RT-TRX-CyN": (make_thermostat, (1,)),
    "BC-TC-C-WM": (make_thermostat, (1,)),
    "HM-CC-RT-DN": (make_thermostat, (4,)),
    "HM-CC-TC": (make_simple_thermostat, (1,)),
    "HM-CC-VG-1": (make_thermostat_group, (1,)),
    "HM-TC-IT-WM-W-EU": (make_thermostat, (2,)),
    "HmIP-BWTH": (make_ip_thermostat, (1,)),
    "HmIP-eTRV": (make_ip_thermostat, (1,)),
    "HmIP-HEATING": (make_ip_thermostat_group, (1,)),
    "HmIP-STH": (make_ip_thermostat, (1,)),
    "HmIP-WTH": (make_ip_thermostat, (1,)),
    "HmIPW-STH": (make_ip_thermostat, (1,)),
    "HmIPW-WTH": (make_ip_thermostat, (1,)),
    "Thermostat AA": (make_ip_thermostat, (1,)),
    "ZEL STG RM FWT": (make_simple_thermostat, (1,)),
}

BLACKLISTED_DEVICES: tuple[str, ...] = ("HmIP-STHO",)
