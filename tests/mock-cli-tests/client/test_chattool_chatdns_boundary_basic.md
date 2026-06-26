# ChatDNS boundary after parent cleanup

## Goal

Verify that ChatTool no longer exposes or owns DNS/certificate business logic after the ChatDNS extraction, while preserving the remote `serve/client cert` shell.

## Cases

### 1. Root DNS command is removed

1. Invoke `chattool dns --help` through the root Click command.
2. Expect a non-zero exit and `No such command`.

### 2. Certificate Python exports are compatibility shims to ChatDNS

1. Import `chatdns.SSLCertUpdater`.
2. Import `chattool.SSLCertUpdater`, `chattool.tools.SSLCertUpdater`, and `chattool.tools.cert.SSLCertUpdater`.
3. Expect all three ChatTool exports to be the same object as `chatdns.SSLCertUpdater`.

### 3. Server cert shell remains lazy-loadable

1. Invoke `chattool serve cert --help` through the root Click command.
2. Expect success and the certificate service options in help output.
3. This should not start uvicorn or touch DNS/ACME.

## Reference script

```sh
python -m pytest -q tests/mock-cli-tests/client/test_chattool_chatdns_boundary_basic.py
```
