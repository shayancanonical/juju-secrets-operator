<!--
Avoid using this README file for information that is maintained or published elsewhere, e.g.:

* metadata.yaml > published on Charmhub
* documentation > published on (or linked to from) Charmhub
* detailed contribution guide > documentation or CONTRIBUTING.md

Use links instead.
-->

# secrets-test

Small demonstration of the unexpected beahvior observed when multiple changes (deletion) are applied on a multi-pack secret of a charm within the smae event context. 


## Description

Demonstration of the issue is visible in the correpsonding [Integration Test](tests/integration/test_charm.py).

NOTE: These tests are representing BROKEN behavior.

Running green means that the feature is still broken.


## How to use

Pipelines are equipped to run both on Juju 3.1. `edge` and `stable` releases.

Whenever a new Juju 3.1. `stable`/`edge` release may be out, you just have to re-run the pipelines to verify if previous issues still may hold.

NOTE: You would want to see ALL tests to FAIL (except the first one marked in the docstring as functional). That means that issues listed here are fully fixed.


## Pipelines

The demo is equipped with verbose pipelines, printing expected results vs. actual ones.

Furthermore, all `juju debug-logs` are also listed after each test run (in case curiousity about the details).

An example of how the demo is showing broken behavior:

```
for i in range(3):
    await helper_execute_action(ops_test, "set-secret", {"key": f"key{i}", "value": f"value{i}"})
await helper_execute_action(ops_test, "delete-secrets", {"keys": ["key{i}" for i in range(3)]})
secrets_data = await helper_execute_action(ops_test, "get-secrets")

# ISSUE: This is NOT the intuitively expected behavior
assert secrets_data.get("secrets") == {"key2": "value2", "key3": "value3"}
```


## Juju Secret issues

At the time of creating the demo, major issues are typically as such:
multiple manipulations within the same event scope applied on a multi-value secret object are not working as expected.

Typically for example when there's an attempt to remove multiple keys from a joined secret -- it's only the first action taking effect.
(Occasionally it's the first and the last action taking effect.)

Similar problems were observed on setting a secret value within a joined secret.
