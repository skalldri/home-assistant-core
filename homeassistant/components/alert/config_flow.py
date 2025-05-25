"""Config flow for Alert integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
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
        # TODO we should allow this to be a list of numbers
        vol.Required(CONF_REPEAT): selector.NumberSelector(
            # TODO figure out how to make a number selector with infinite upper bound
            config=selector.NumberSelectorConfig(
                min=0.016, max=10000000, mode=selector.NumberSelectorMode.BOX
            ),
        ),
        # vol.All(
        #     cv.ensure_list,
        #     [vol.Coerce(float)],
        #     # Minimum delay is 1 second = 0.016 minutes
        #     [vol.Range(min=0.016)],
        # ),
        vol.Optional(CONF_CAN_ACK, default=DEFAULT_CAN_ACK): selector.BooleanSelector(),
        vol.Optional(
            CONF_SKIP_FIRST, default=DEFAULT_SKIP_FIRST
        ): selector.BooleanSelector(),
        vol.Optional(CONF_ALERT_MESSAGE): cv.string,
        vol.Optional(CONF_DONE_MESSAGE): cv.string,
        vol.Optional(CONF_TITLE): cv.string,
        # TODO how do we do dicts? this doesn't work
        # vol.Optional(CONF_DATA): dict,
        # TODO notifier selector???
        vol.Optional(CONF_NOTIFIERS, default=[]): selector.EntitySelector(
            config=selector.EntitySelectorConfig(domain="notify", multiple=True)
        ),
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): selector.EntitySelector(),
        vol.Optional(CONF_STATE, default=STATE_ON): cv.string,
        # TODO we should allow this to be a list of numbers
        vol.Required(CONF_REPEAT): selector.NumberSelector(
            # TODO figure out how to make a number selector with infinite upper bound
            config=selector.NumberSelectorConfig(
                min=0.016, max=10000000, mode=selector.NumberSelectorMode.BOX
            ),
        ),
        # vol.All(
        #     cv.ensure_list,
        #     [vol.Coerce(float)],
        #     # Minimum delay is 1 second = 0.016 minutes
        #     [vol.Range(min=0.016)],
        # ),
        vol.Optional(CONF_CAN_ACK, default=DEFAULT_CAN_ACK): selector.BooleanSelector(),
        vol.Optional(
            CONF_SKIP_FIRST, default=DEFAULT_SKIP_FIRST
        ): selector.BooleanSelector(),
        vol.Optional(CONF_ALERT_MESSAGE): cv.string,
        vol.Optional(CONF_DONE_MESSAGE): cv.string,
        vol.Optional(CONF_TITLE): cv.string,
        # TODO how do we do dicts? this doesn't work
        # vol.Optional(CONF_DATA): dict,
        # TODO notifier selector???
        vol.Optional(CONF_NOTIFIERS, default=[]): selector.EntitySelector(
            config=selector.EntitySelectorConfig(domain="notify", multiple=True)
        ),
    }
)

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(
        CONFIG_SCHEMA,
        validate_user_input=_validate_input,
    ),
}


class AlertConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle Alert config flow."""

    config_flow = CONFIG_FLOW

    @callback
    def async_config_entry_title(self, options: dict[str, Any]) -> str:
        """Return config entry title."""
        return options[CONF_NAME]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        ##return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA)
        return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> AlertOptionsFlowHandler:
        """Return the options flow."""
        return AlertOptionsFlowHandler()


class AlertOptionsFlowHandler(OptionsFlow):
    """Handle Alert options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
        )
