#!/usr/bin/env python3
# Copyright 2023 Shayan
# See LICENSE file for licensing details.

import asyncio
import logging
from pathlib import Path
from typing import Optional

import pytest
import yaml
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)

METADATA = yaml.safe_load(Path("./metadata.yaml").read_text())
APP_NAME = METADATA["name"]
UNIT0_NAME = f"{APP_NAME}/0"


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest):
    """Build the charm-under-test and deploy it together with related charms.

    Assert on the unit status before any relations/configurations take place.
    """
    # Build and deploy charm from local source folder
    charm = await ops_test.build_charm(".")
    resources = {
        "secrets-test-image": METADATA["resources"]["secrets-test-image"]["upstream-source"]
    }

    # Deploy the charm and wait for active/idle status
    await asyncio.gather(
        ops_test.model.deploy(charm, resources=resources, application_name=APP_NAME),
        ops_test.model.wait_for_idle(
            apps=[APP_NAME], status="active", raise_on_blocked=True, timeout=1000
        ),
    )


async def helper_execute_action(
    ops_test: OpsTest, action: str, params: Optional[dict[str, str]] = None
):
    if params:
        action = await ops_test.model.units.get(UNIT0_NAME).run_action(action, **params)
    else:
        action = await ops_test.model.units.get(UNIT0_NAME).run_action(action)
    action = await action.wait()
    return action.results


async def test_delete_secret(ops_test: OpsTest):
    """Testing if it's possible to remove a secret from a joined secret removing one-by-one.

    NOTE: This should work
    """
    await helper_execute_action(ops_test, "forget-all-secrets")

    await helper_execute_action(ops_test, "set-secret", {"key": "key1", "value": "value1"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key2", "value": "value2"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key3", "value": "value3"})

    secrets_data = await helper_execute_action(ops_test, "get-secrets")

    assert secrets_data["secrets"] == {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
    }

    await helper_execute_action(ops_test, "set-secret", {"key": "key1"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key2"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key3"})

    secrets_data = await helper_execute_action(ops_test, "get-secrets")

    # NOTE: event.set_results() removes keys with empty values
    assert "secrets" not in secrets_data


async def test_delete_all_secrets_within_the_same_action_scope(ops_test: OpsTest):
    """Testing if it's possible to remove a secret from a joined secret removing one-by-one within the same event scope.

    NOTE: This should fail
    """
    await helper_execute_action(ops_test, "forget-all-secrets")

    await helper_execute_action(ops_test, "set-secret", {"key": "key1", "value": "value1"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key2", "value": "value2"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key3", "value": "value3"})

    await helper_execute_action(ops_test, "delete-secrets", {"keys": ["key1", "key2", "key3"]})

    secrets_data = await helper_execute_action(ops_test, "get-secrets")

    #
    # The issue still holds :-( :-( :-(
    # Should be {}
    #
    assert secrets_data.get("secrets") == {
            "key2": "value2",
            "key3": "value3",
    }


async def test_delete_secrets_within_the_same_action_scope(ops_test: OpsTest):
    """Testing if it's possible to remove a secret from a joined secret removing one-by-one within the same event scope.

    NOTE: This should fail
    """
    await helper_execute_action(ops_test, "forget-all-secrets")

    await helper_execute_action(ops_test, "set-secret", {"key": "key1", "value": "value1"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key2", "value": "value2"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key3", "value": "value3"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key4", "value": "value4"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key5", "value": "value5"})

    await helper_execute_action(ops_test, "delete-secrets", {"keys": ["key1", "key3", "key5"]})

    secrets_data = await helper_execute_action(ops_test, "get-secrets")

    #
    # The issue still holds :-(
    # Should be {"key2": "password2", "key4": "password4"}
    #
    assert secrets_data.get("secrets") == {
            "key2": "value2",
            "key3": "value3",
            "key4": "value4",
            "key5": "value5",
    }


async def test_set_all_secrets_within_the_same_action_scope_work_fine(ops_test: OpsTest):
    """Testing if it's possible to remove a secret from a joined secret removing one-by-one within the same event scope.

    NOTE: This should fail
    """
    await helper_execute_action(ops_test, "forget-all-secrets")

    await helper_execute_action(ops_test, "set-secret", {"key": "key1", "value": "value1"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key2", "value": "value2"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key3", "value": "value3"})

    await helper_execute_action(ops_test, "pseudo-delete-secrets", {"keys": ["key1", "key2", "key3"]})

    secrets_data = await helper_execute_action(ops_test, "get-secrets")

    #
    # ISSUE!!!!! "key2" should be '### DELETED ###'
    #
    assert secrets_data.get("secrets") == {
            "key1": "### DELETED ###",
            "key2": "value2",
            "key3": "### DELETED ###",
    }


async def test_set_secrets_within_the_same_action_scope_works(ops_test: OpsTest):
    """Testing if it's possible to remove a secret from a joined secret removing one-by-one within the same event scope.

    NOTE: This should fail
    """
    await helper_execute_action(ops_test, "forget-all-secrets")

    await helper_execute_action(ops_test, "set-secret", {"key": "key1", "value": "value1"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key2", "value": "value2"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key3", "value": "value3"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key4", "value": "value4"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key5", "value": "value5"})

    await helper_execute_action(ops_test, "pseudo-delete-secrets", {"keys": ["key1", "key3", "key5"]})

    secrets_data = await helper_execute_action(ops_test, "get-secrets")

    #
    # ISSUE!!!!! "key3" should be '### DELETED ###'
    #
    assert secrets_data.get("secrets") == {
            "key1": "### DELETED ###",
            "key2": "value2",
            "key3": "value3",
            "key4": "value4",
            "key5": "### DELETED ###",
    }
