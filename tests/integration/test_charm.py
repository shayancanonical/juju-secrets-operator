#!/usr/bin/env python3
# Copyright 2023 Shayan
# See LICENSE file for licensing details.

import asyncio
import logging
import json
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


async def test_delete_secret_within_separate_event_scopes_always_works(ops_test: OpsTest):
    """Testing if it's possible to remove all keys from a joined secret one-by-one in SEPARATE event scopes.

    NOTE: This functionality is OK
    """
    await helper_execute_action(ops_test, "forget-all-secrets")

    content = {f"key{i}": f"value{i}" for i in range(3)}
    await helper_execute_action(ops_test, "set-secret", content)

    secrets_data = await helper_execute_action(ops_test, "get-secrets")

    assert secrets_data["secrets"] == {
        "key0": "value0",
        "key1": "value1",
        "key2": "value2",
    }

    for i in range(3):
        await helper_execute_action(ops_test, "delete-secrets", {"keys": [f"key{i}"]})

    secrets_data = await helper_execute_action(ops_test, "get-secrets")

    # NOTE: event.set_results() removes keys with empty values
    assert "secrets" not in secrets_data


async def test_delete_all_secrets_within_the_same_action_scope(ops_test: OpsTest):
    """Testing if it's possible to remove all keys from a joined secret removing one-by-one within the same event scope.
    """
    await helper_execute_action(ops_test, "forget-all-secrets")

    content = {f"key{i}": f"value{i}" for i in range(3)}
    await helper_execute_action(ops_test, "set-secret", content)

    await helper_execute_action(ops_test, "delete-secrets", {"keys": [f"key{i}" for i in range(3)]})

    secrets_data = await helper_execute_action(ops_test, "get-secrets")

    secrets = secrets_data.get("secrets")
    # ISSUE!!!!! Empty dict wouldn't have made it to event results
    assert secrets

    print()
    print("*************************************************************************")
    print("All keys should be deleted [0..2].")
    print(f"Actual results: {json.dumps(secrets, sort_keys=True, indent=4)}")
    print("*************************************************************************")


async def test_delete_secrets_within_the_same_action_scope(ops_test: OpsTest):
    """Testing if it's possible to remove keys from a joined secret one-by-one within the same event scope.

    NOTE: This should fail
    """
    await helper_execute_action(ops_test, "forget-all-secrets")

    content = {f"key{i}": f"value{i}" for i in range(5)}
    await helper_execute_action(ops_test, "set-secret", content)

    await helper_execute_action(ops_test, "delete-secrets", {"keys": [f"key{i}" for i in range(0, 5, 2)]})

    secrets_data = await helper_execute_action(ops_test, "get-secrets")

    secrets = secrets_data.get("secrets")
    # ISSUE!!!!! Empty dict wouldn't have made it to event results
    assert secrets
    assert 2 < len(secrets.keys())

    print()
    print("*************************************************************************")
    print("Even keys should be deleted [0..4].")
    print(f"Actual results: {json.dumps(secrets, sort_keys=True, indent=4)}")
    print("*************************************************************************")


async def test_set_all_secrets_within_the_same_action_scope_work_fine(ops_test: OpsTest):
    """Testing if it's possible to set all values within a joined secret one-by-one within the same event scope.

    NOTE: This should fail
    """
    await helper_execute_action(ops_test, "forget-all-secrets")

    content = {f"key{i}": f"value{i}" for i in range(5)}
    await helper_execute_action(ops_test, "set-secret", content)

    await helper_execute_action(ops_test, "pseudo-delete-secrets", {"keys": [f"key{i}" for i in range(5)]})

    secrets_data = await helper_execute_action(ops_test, "get-secrets")

    secrets = secrets_data.get("secrets")
    assert 0 < sum([secrets[key] != "### DELETED ###" for key in secrets])

    print()
    print("*************************************************************************")
    print("All keys should be marked as deleted [0..4].")
    print(f"Actual results: {json.dumps(secrets, sort_keys=True, indent=4)}")
    print("*************************************************************************")


async def test_set_secrets_within_the_same_action_scope_works(ops_test: OpsTest):
    """Testing if it's possible to set a some values within a joined secret one-by-one within the same event scope.

    NOTE: This should fail
    """
    await helper_execute_action(ops_test, "forget-all-secrets")

    content = {f"key{i}": f"value{i}" for i in range(5)}
    await helper_execute_action(ops_test, "set-secret", content)

    await helper_execute_action(ops_test, "pseudo-delete-secrets", {"keys": [f"key{i}" for i in range(0, 5, 2)]})

    secrets_data = await helper_execute_action(ops_test, "get-secrets")

    # ISSUE!!!!! "key3" should be '### DELETED ###'
    secrets = secrets_data.get("secrets")
    assert 2 < sum([secrets[key] != "### DELETED ###" for key in secrets])

    print()
    print("*************************************************************************")
    print("Even keys should be marked as deleted [0..4].")
    print(f"Actual results: {json.dumps(secrets_data.get('secrets'), sort_keys=True, indent=4)}")
    print("*************************************************************************")


async def test_delete_lotta_secrets_within_the_same_action_scope(ops_test: OpsTest):
    """Testing if it's possible to remove keys from a joined secret one-by-one within the same event scope.

    NOTE: This should fail
    """
    await helper_execute_action(ops_test, "forget-all-secrets")

    content = {f"key{i}": f"value{i}" for i in range(15)}
    await helper_execute_action(ops_test, "set-secret", content)

    await helper_execute_action(ops_test, "delete-secrets", {"keys": [f"key{i}" for i in range(15)]})

    secrets_data = await helper_execute_action(ops_test, "get-secrets")

    secrets = secrets_data.get("secrets")
    # ISSUE!!!!! Empty dict wouldn't have made it to event results
    assert secrets

    print()
    print("*************************************************************************")
    print("Keys ([0..14]) all deleted.")
    print(f"Actual results: {json.dumps(secrets, sort_keys=True, indent=4)}")
    print("*************************************************************************")


async def test_set_lotta_secrets_within_the_same_action_scope(ops_test: OpsTest):
    """Testing if it's possible to remove a keys from a joined secret one-by-one within the same event scope.

    NOTE: This should fail
    """
    await helper_execute_action(ops_test, "forget-all-secrets")

    content = {f"key{i}": f"value{i}" for i in range(15)}
    await helper_execute_action(ops_test, "set-secret", content)

    await helper_execute_action(ops_test, "pseudo-delete-secrets", {"keys": [f"key{i}" for i in range(15)]})

    secrets_data = await helper_execute_action(ops_test, "get-secrets")

    secrets = secrets_data.get("secrets")
    # ISSUE!!!!! Empty dict wouldn't have made it to event results
    assert secrets
    assert 0 < sum([f"key{i}" != "### DELETED ###" for i in range(15)])

    print()
    print("*************************************************************************")
    print("Keys [0..14] were all marked as deleted.")
    print(f"Actual results: {json.dumps(secrets, sort_keys=True, indent=4)}")
    print("*************************************************************************")
