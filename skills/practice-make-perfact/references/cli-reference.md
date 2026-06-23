# ChatTool CLI Reference For Post-Task Cleanup

Use this as a quick index before adding ad hoc scripts or new instructions.

## Package Helpers

```bash
chattool pypi init <name>
chattool pypi init <name> -t chatarch --project-dir ./<name>
chattool pypi build --project-dir .
chattool pypi check --project-dir .
chattool pypi probe <name>
chattool pypi upload --project-dir .
chatpypi <name> -t chatarch --project-dir ./<name>
```

`chatpypi <name>` is a convenience wrapper for `chattool pypi init <name>` when `<name>` is not a known pypi subcommand.

## Skill Helpers

```bash
chattool skill list --source ChatTool/skills
chattool skill install <name> --source ChatTool/skills --platform codex --force
chattool skill install --all --source ChatTool/skills --dest /tmp/skills --platform codex --force
```

Supported install platforms are `codex`, `claude`, and `opencode`.

## Env/Profile Helpers

```bash
chatenv init -t <type>
chatenv list
chatenv cat -t <type>
chatenv new -t <type> work
chatenv save -t <type> work
chatenv use -t <type> work
chatenv delete -t <type> work
chatenv paste --stdin --profile work
chatenv test -t <type>
```

Business packages register schemas through `[project.entry-points."chatenv.configs"]`.

## GitHub Helpers

```bash
chatgh pr list --repo owner/repo --state open --limit 20
chatgh pr view 123 --repo owner/repo
chatgh pr checks 123 --repo owner/repo
chatgh run view --repo owner/repo --run-id 123
chatgh run logs --repo owner/repo --job-id 456
# PR create/edit/merge are not public stable ChatGH CLI commands yet; use the project workflow or GitHub API path for those writes.
```

## DNS And Certificates

```bash
chattool dns list
chattool dns records --domain example.com
chattool dns set --domain example.com --rr www --type A --value 1.2.3.4
chattool dns delete --domain example.com --rr www --type A --yes
chattool dns ip
chattool dns ddns
chattool dns cert apply -d example.com -e admin@example.com -p aliyun
chattool dns cert check -d example.com --cert-dir certs
```

MCP tool names include `dns_list_domains`, `dns_get_records`, `dns_add_record`, `dns_delete_record`, `dns_ddns_update`, and `dns_cert_apply`.
