#!/usr/bin/env python3
# Copyright 2023 Shayan
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

https://discourse.charmhub.io/t/4208
"""

import logging

import ops
from ops.charm import ActionEvent

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)

VALID_LOG_LEVELS = ["info", "debug", "warning", "error", "critical"]
PEER = "charm-peer"


class SecretsTestCharm(ops.CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)

        self.framework.observe(self.on.set_secret_action, self._on_set_secret_action)
        self.framework.observe(self.on.get_secrets_action, self._on_get_secrets_action)

    def _on_set_secret_action(self, event: ActionEvent):
        key, value = event.params.get("key"), event.params.get("value")
        self.set_secret(key, value)

    def _on_get_secrets_action(self, event: ActionEvent):
        """Return the secrets stored in juju secrets backend."""
        event.set_results({"secrets": self.get_secrets()})

    @property
    def peers(self) -> ops.model.Relation:
        """Retrieve the peer relation (`ops.model.Relation`)."""
        return self.model.get_relation(PEER)

    @property
    def app_peer_data(self) -> dict[str, str]:
        """Application peer relation data object."""
        if self.peers is None:
            return {}

        return self.peers.data[self.app]

    def get_secrets(self) -> dict[str, str]:
        """Get the secrets stored in juju secrets backend."""
        secret_id = self.app_peer_data.get("secret-id")
            
        if not secret_id:
            return {}

        secret = self.model.get_secret(id=secret_id)
        content = secret.get_content()
        logger.info(f"Retrieved secret {secret_id} with content {content}")
        return content

    def set_secret(self, key: str, value: str) -> None:
        """Set the secret in the juju secret storage."""
        secret_id = self.app_peer_data.get("secret-id")

        content = {
            key: value,
        }

        if secret_id:
            secret = self.model.get_secret(id=secret_id)
            logger.info(f"Setting secret {secret.id} to {content}")
            secret.set_content(content)
        else:
            secret = self.app.add_secret(content)
            self.app_peer_data["secret-id"] = secret.id
            logger.info(f"Added secret {secret.id} to {content}")


if __name__ == "__main__":  # pragma: nocover
    ops.main(SecretsTestCharm)
