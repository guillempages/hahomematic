"""
Module for entities implemented using the
select platform (https://www.home-assistant.io/integrations/select/).
"""
from __future__ import annotations

import logging
from typing import Union

from hahomematic.const import HmPlatform
from hahomematic.decorators import value_property
from hahomematic.entity import GenericEntity, GenericSystemVariable

_LOGGER = logging.getLogger(__name__)


# pylint: disable=consider-alternative-union-syntax
class HmSelect(GenericEntity[Union[int, str]]):
    """
    Implementation of a select entity.
    This is a default platform that gets automatically generated.
    """

    _attr_platform = HmPlatform.SELECT

    @value_property
    def value(self) -> str | None:  # type: ignore[override]
        """Get the value of the entity."""
        if self._attr_value is not None and self._attr_value_list is not None:
            return self._attr_value_list[int(self._attr_value)]
        return str(self._attr_default)

    async def send_value(self, value: int | str) -> None:
        """Set the value of the entity."""
        # We allow setting the value via index as well, just in case.
        if isinstance(value, int) and self._attr_value_list:
            if 0 <= value < len(self._attr_value_list):
                await super().send_value(value)
                return None
        elif self._attr_value_list:
            if value in self._attr_value_list:
                await super().send_value(self._attr_value_list.index(value))
                return None

        _LOGGER.warning(
            "Value not in value_list for %s/%s.",
            self.name,
            self.unique_identifier,
        )


class HmSysvarSelect(GenericSystemVariable):
    """
    Implementation of a sysvar select entity.
    """

    _attr_platform = HmPlatform.HUB_SELECT
    _attr_is_extended = True

    @value_property
    def value(self) -> str | None:
        """Get the value of the entity."""
        if self._attr_value is not None and self._attr_value_list is not None:
            return self._attr_value_list[int(self._attr_value)]
        return None

    async def send_variable(self, value: int | str) -> None:
        """Set the value of the entity."""
        # We allow setting the value via index as well, just in case.
        if isinstance(value, int) and self._attr_value_list:
            if 0 <= value < len(self._attr_value_list):
                await super().send_variable(value)
                return None
        elif self._attr_value_list:
            if value in self._attr_value_list:
                await super().send_variable(self._attr_value_list.index(value))
                return None

        _LOGGER.warning(
            "Value not in value_list for %s/%s.",
            self.name,
            self.unique_identifier,
        )
