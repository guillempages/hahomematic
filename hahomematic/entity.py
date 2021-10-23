# pylint: disable=line-too-long

"""
Functions for entity creation.
"""

import logging
from abc import ABC, abstractmethod

from hahomematic.const import (
    ATTR_HM_CONTROL,
    ATTR_HM_MAX,
    ATTR_HM_MIN,
    ATTR_HM_OPERATIONS,
    ATTR_HM_SPECIAL,
    ATTR_HM_TYPE,
    ATTR_HM_UNIT,
    ATTR_HM_VALUE_LIST,
    HA_DOMAIN,
    TYPE_ACTION,
)

LOG = logging.getLogger(__name__)

# pylint: disable=too-many-instance-attributes
class BaseEntity(ABC):
    """
    Base class for regular entities.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        server,
        interface_id,
        unique_id,
        address,
        platform,
    ):
        """
        Initialize the entity.
        :param server:
        """
        self._server = server
        self.interface_id = interface_id
        self.client = self._server.clients[interface_id]
        self.proxy = self.client.proxy
        self.unique_id = unique_id
        self.platform = platform
        self.address = address
        self._parent_address = address.split(":")[0]
        self._parent_device = self._server.devices_raw_dict[interface_id][
            self._parent_address
        ]
        self.device_type = self._parent_device.get(ATTR_HM_TYPE)
        self.device_class = None

        self._update_callback = None
        self._remove_callback = None

    def register_update_callback(self, update_callback):
        """register update callback"""
        if callable(update_callback):
            self._update_callback = update_callback

    def unregister_update_callback(self):
        """remove update callback"""
        self._update_callback = None

    def update_entity(self):
        """
        Do what is needed when the state of the entity has been updated.
        """
        if self._update_callback is None:
            LOG.debug("Entity.update_entity: No callback defined.")
            return
        # pylint: disable=not-callable
        self._update_callback(self.unique_id)

    def register_remove_callback(self, remove_callback):
        """register remove callback"""
        if callable(remove_callback):
            self._remove_callback = remove_callback

    def unregister_remove_callback(self):
        """remove remove callback"""
        self._remove_callback = None

    def remove_entity(self):
        """
        Do what is needed when the entity has been removed.
        """
        if self._remove_callback is None:
            LOG.debug("Entity.remove_entity: No callback defined.")
            return
        # pylint: disable=not-callable
        self._remove_entity(self.unique_id)

    @property
    def device_info(self):
        """Return device specific attributes."""
        return {
            "identifiers": {(HA_DOMAIN, self._parent_address)},
            "name": self._server.ha_devices.get(self._parent_address).name,
            "manufacturer": "eQ-3",
            "model": self.device_type,
            "sw_version": self._parent_device.get("FIRMWARE"),
            "via_device": (HA_DOMAIN, self.interface_id),
        }


class GenericEntity(BaseEntity):
    """
    Base class for generic entities.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        server,
        interface_id,
        unique_id,
        address,
        parameter,
        parameter_data,
        platform,
    ):
        """
        Initialize the entity.
        :param server:
        """
        super().__init__(server, interface_id, unique_id, address, platform)

        self._parent_address = address.split(":")[0]
        self._parent_device = self._server.devices_raw_dict[interface_id][
            self._parent_address
        ]
        self.parameter = parameter
        self._parameter_data = parameter_data
        self.name = self._name()
        self.operations = self._parameter_data.get(ATTR_HM_OPERATIONS)
        self.type = self._parameter_data.get(ATTR_HM_TYPE)
        self.control = self._parameter_data.get(ATTR_HM_CONTROL)
        self.unit = self._parameter_data.get(ATTR_HM_UNIT)
        self.max = self._parameter_data.get(ATTR_HM_MAX)
        self.min = self._parameter_data.get(ATTR_HM_MIN)
        self.value_list = self._parameter_data.get(ATTR_HM_VALUE_LIST)
        self.special = self._parameter_data.get(ATTR_HM_SPECIAL)

        self._state = None
        if self.type == TYPE_ACTION:
            self._state = False

        LOG.debug("Entity.__init__: Getting current value for %s", self.unique_id)
        # pylint: disable=pointless-statement
        # self.STATE
        self._server.event_subscriptions[(self.address, self.parameter)].append(
            self.event
        )

    def event(self, interface_id, address, parameter, value):
        """
        Handle event for which this entity has subscribed.
        """
        LOG.debug(
            "Entity.event: %s, %s, %s, %s", interface_id, address, parameter, value
        )
        if interface_id != self.interface_id:
            LOG.warning(
                "Entity.event: Incorrect interface_id: %s - should be: %s",
                interface_id,
                self.interface_id,
            )
            return
        if address != self.address:
            LOG.warning(
                "Entity.event: Incorrect address: %s - should be: %s",
                address,
                self.address,
            )
            return
        if parameter != self.parameter:
            LOG.warning(
                "Entity.event: Incorrect parameter: %s - should be: %s",
                parameter,
                self.parameter,
            )
            return
        self._state = value
        self.update_entity()


    @property
    @abstractmethod
    # pylint: disable=invalid-name,missing-function-docstring
    def STATE(self):
        ...

    def _name(self):
        name = self.client.server.names_cache.get(self.interface_id, {}).get(
            self.address, self.unique_id
        )
        if name.count(':') == 1:
            d_name = name.split(':')[0]
            p_name = self.parameter.title().replace('_',' ')
            c_no = name.split(':')[1]
            c_name = "" if c_no == "0" else f" ch{c_no}"
            return f"{d_name} {p_name}{c_name}"
        else:
            return name
