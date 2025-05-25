"""Support for repeating alerts when conditions are met."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_REPEAT,
    CONF_STATE,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType
from homeassistant.util.hass_dict import HassKey

from .const import (
    CONF_ALERT_MESSAGE,
    CONF_CAN_ACK,
    CONF_DATA,
    CONF_DONE_MESSAGE,
    CONF_NOTIFIERS,
    CONF_SKIP_FIRST,
    CONF_TITLE,
    DEFAULT_CAN_ACK,
    DEFAULT_SKIP_FIRST,
    DOMAIN,
    LOGGER,
)
from .entity import AlertEntity

ALERT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Optional(CONF_STATE, default=STATE_ON): cv.string,
        vol.Required(CONF_REPEAT): vol.All(
            cv.ensure_list,
            [vol.Coerce(float)],
            # Minimum delay is 1 second = 0.016 minutes
            [vol.Range(min=0.016)],
        ),
        vol.Optional(CONF_CAN_ACK, default=DEFAULT_CAN_ACK): cv.boolean,
        vol.Optional(CONF_SKIP_FIRST, default=DEFAULT_SKIP_FIRST): cv.boolean,
        vol.Optional(CONF_ALERT_MESSAGE): cv.template,
        vol.Optional(CONF_DONE_MESSAGE): cv.template,
        vol.Optional(CONF_TITLE): cv.template,
        vol.Optional(CONF_DATA): dict,
        vol.Optional(CONF_NOTIFIERS, default=list): vol.All(
            cv.ensure_list, [cv.string]
        ),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: cv.schema_with_slug_keys(ALERT_SCHEMA)}, extra=vol.ALLOW_EXTRA
)

type AlertConfigEntry = ConfigEntry[AlertData]


@dataclass
class AlertData:
    """Runtime data for the Alert class."""

    name: str


# async def async_setup_entry(
#    hass: HomeAssistant, config_entry: AlertConfigEntry
# ) -> bool:
#    return True


DATA_COMPONENT: HassKey[EntityComponent[AlertEntity]] = HassKey(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Alert component."""
    component = hass.data[DATA_COMPONENT] = EntityComponent[AlertEntity](
        LOGGER, DOMAIN, hass
    )

    await component.async_setup(config)

    if DOMAIN not in config:
        return True

    entities: list[AlertEntity] = []

    for object_id, cfg in config[DOMAIN].items():
        if not cfg:
            cfg = {}

        name = cfg[CONF_NAME]
        watched_entity_id = cfg[CONF_ENTITY_ID]
        alert_state = cfg[CONF_STATE]
        repeat = cfg[CONF_REPEAT]
        skip_first = cfg[CONF_SKIP_FIRST]
        message_template = cfg.get(CONF_ALERT_MESSAGE)
        done_message_template = cfg.get(CONF_DONE_MESSAGE)
        notifiers = cfg[CONF_NOTIFIERS]
        can_ack = cfg[CONF_CAN_ACK]
        title_template = cfg.get(CONF_TITLE)
        data = cfg.get(CONF_DATA)

        entities.append(
            AlertEntity(
                hass,
                object_id,
                name,
                watched_entity_id,
                alert_state,
                repeat,
                skip_first,
                message_template,
                done_message_template,
                notifiers,
                can_ack,
                title_template,
                data,
            )
        )

    await component.async_add_entities(entities)

    component.async_register_entity_service(SERVICE_TURN_OFF, None, "async_turn_off")
    component.async_register_entity_service(SERVICE_TURN_ON, None, "async_turn_on")
    component.async_register_entity_service(SERVICE_TOGGLE, None, "async_toggle")

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Alert from a config entry."""

    # From what I'm gathering...
    # It seems like these "entry" already have a backing entity
    # we just need to setup callbacks and such to make the alert function
    # .... seems that way?

    data = dict(entry.data)

    # If options exist, they take precedence over data
    # TODO wtf is this
    # if entry.options:
    #     data.update(entry.options)

    entry.runtime_data = AlertEntity(
        hass,
        entry.entry_id,  ## UNUSED
        data[CONF_NAME],  # Required
        data[CONF_ENTITY_ID],  # Required
        data[CONF_STATE],  # Optional, but has a default
        # TODO: this should be a list from the config level, but I can't figure it out
        [data[CONF_REPEAT]],  # Required
        data[CONF_SKIP_FIRST],  # Optional, but has a default
        data.get(CONF_ALERT_MESSAGE, None),
        data.get(CONF_DONE_MESSAGE, None),
        data[CONF_NOTIFIERS],  # Options, has a default
        data[CONF_CAN_ACK],
        data.get(CONF_TITLE, None),
        data.get(CONF_DATA, {}),
    )

    # No need to create a new entity, one is already created
    # await hass.data[DATA_COMPONENT].async_add_entities([entity])

    # Register update listener to handle options updates
    entry.async_on_unload(entry.add_update_listener(config_entry_update_listener))

    return True


async def config_entry_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener, called when the config entry options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)

    for entity in entities:
        await entity_registry.async_remove(entity.entity_id)

    return True
