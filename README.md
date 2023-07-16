<!--
Avoid using this README file for information that is maintained or published elsewhere, e.g.:

* metadata.yaml > published on Charmhub
* documentation > published on (or linked to from) Charmhub
* detailed contribution guide > documentation or CONTRIBUTING.md

Use links instead.
-->

# secrets-test

Small demonstration of the unexpected beahvior observed when multiple changes (deletion) are applied on a multi-pack secret of a charm within the smae event context. 

## Issue

Demonstration of the issue is visible in the correpsonding [Integration Test](tests/integration/test_charm.py) -- run successfully by the corresponding pipeline.

```
async def test_delete_secrets_within_the_same_action_scope(ops_test: OpsTest):
    """Testing if it's possible to remove a secret from a joined secret removing one-by-one.

    NOTE: This should work
    """
    await helper_execute_action(ops_test, "set-secret", {"key": "key1", "value": "value1"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key2", "value": "value2"})
    await helper_execute_action(ops_test, "set-secret", {"key": "key3", "value": "value3"})

    await helper_execute_action(ops_test, "delete-secrets", {"keys": ["key1", "key2", "key3"]})

    secrets_data = await helper_execute_action(ops_test, "get-secrets")

    #   
    # ISSUE: This is NOT the intuitively expected behavior
    #   
    assert secrets_data.get("secrets") == {"key2": "value2", "key3": "value3"}
