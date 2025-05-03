"""Config flow for Alert integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.const import (
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_REPEAT,
    CONF_STATE,
    STATE_ON,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv, selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
)

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
)


async def _get_notifiers(hass: HomeAssistant) -> list[str]:
    """Return a list of notifiers."""
    return [
        notifier
        for notifier in hass.services.async_services().get(NOTIFY_DOMAIN, {})
        if notifier != "persistent_notification"
    ]


async def _validate_input(
    handler: SchemaConfigFlowHandler, user_input: dict[str, Any]
) -> dict[str, Any]:
    """Validate if the user input can be processed."""
    # Convert notify entities to a list if a string is passed
    if notifiers := user_input.get(CONF_NOTIFIERS):
        if isinstance(notifiers, str):
            user_input[CONF_NOTIFIERS] = [notifiers]
    return user_input


CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_ENTITY_ID): selector.EntitySelector(),
        vol.Optional(CONF_STATE, default=STATE_ON): cv.string,
        vol.Required(CONF_REPEAT): vol.All(
            cv.ensure_list,
            [vol.Coerce(float)],
            # Minimum delay is 1 second = 0.016 minutes
            [vol.Range(min=0.016)],
        ),
        vol.Optional(CONF_CAN_ACK, default=DEFAULT_CAN_ACK): selector.BooleanSelector(),
        vol.Optional(
            CONF_SKIP_FIRST, default=DEFAULT_SKIP_FIRST
        ): selector.BooleanSelector(),
        vol.Optional(CONF_ALERT_MESSAGE): cv.string,
        vol.Optional(CONF_DONE_MESSAGE): cv.string,
        vol.Optional(CONF_TITLE): cv.string,
        vol.Optional(CONF_DATA): dict,
        vol.Optional(CONF_NOTIFIERS, default=[]): vol.All(cv.ensure_list, [cv.string]),
    }
)

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(
        CONFIG_SCHEMA,
        validate_user_input=_validate_input,
    ),
}


class AlertConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle Alert config flow."""

    config_flow = CONFIG_FLOW

    @callback
    def async_config_entry_title(self, options: dict[str, Any]) -> str:
        """Return config entry title."""
        return options[CONF_NAME]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            schema = self.add_suggested_values_to_schema(CONFIG_SCHEMA, {})
            available_notifiers = await _get_notifiers(self.hass)
            schema = schema.extend(
                {
                    vol.Optional(CONF_NOTIFIERS, default=[]): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"label": notifier, "value": notifier}
                                for notifier in available_notifiers
                            ],
                            multiple=True,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            )
            return self.async_show_form(step_id="user", data_schema=schema)

        errors = {}

        # Add additional validation as needed
        user_input = await _validate_input(self, user_input)

        if not errors:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(CONFIG_SCHEMA, user_input),
            errors=errors,
        )

    @classmethod
    @callback
    def async_get_options_flow(cls, config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return AlertOptionsFlowHandler(config_entry)


class AlertOptionsFlowHandler(SchemaConfigFlowHandler):
    """Handle Alert options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        super().__init__(config_entry.options)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is None:
            schema = self.add_suggested_values_to_schema(
                CONFIG_SCHEMA, self.config_entry.data
            )
            available_notifiers = await _get_notifiers(self.hass)
            schema = schema.extend(
                {
                    vol.Optional(CONF_NOTIFIERS, default=[]): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"label": notifier, "value": notifier}
                                for notifier in available_notifiers
                            ],
                            multiple=True,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            )
            return self.async_show_form(step_id="init", data_schema=schema)

        errors = {}

        # Add additional validation as needed
        user_input = await _validate_input(self, user_input)

        if not errors:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(CONFIG_SCHEMA, user_input),
            errors=errors,
        )
