from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import importlib
import json
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import textwrap
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


DEFAULT_DIST_DIRNAME = "dist"
LICENSE_TEMPLATES = {
    "MIT": """MIT License

Copyright (c) {year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",
    "Apache-2.0": """Apache License
Version 2.0, January 2004
https://www.apache.org/licenses/

Copyright {year} {author}

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
""",
    "BSD-3-Clause": """BSD 3-Clause License

Copyright (c) {year}, {author}
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE.
""",
    "GPL-3.0-only": """GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (c) {year} {author}

This project is licensed under the GNU General Public License version 3.
See https://www.gnu.org/licenses/gpl-3.0.en.html for the full license text.
""",
    "Proprietary": """Proprietary License

Copyright (c) {year} {author}. All rights reserved.

This software is proprietary and confidential. Unauthorized copying,
distribution, modification, or use of this software is prohibited without
prior written permission.
""",
}


class PyPICommandError(RuntimeError):
    """Raised when a package operation cannot be completed safely."""


@dataclass
class ProjectMetadata:
    name: str | None
    version: str | None
    version_source: str | None
    readme: str | None
    requires_python: str | None
    license_text: str | None
    dynamic_fields: list[str]


@dataclass
class DoctorCheck:
    label: str
    status: str
    detail: str
    hint: str | None = None


@dataclass
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str


@dataclass
class ScaffoldResult:
    project_dir: Path
    package_name: str
    module_name: str
    created_files: list[Path]


@dataclass
class RepositoryCheck:
    label: str
    status: str
    detail: str
    hint: str | None = None


def _extract_project_snippets(payload: dict | None) -> list[RepositoryCheck]:
    if not isinstance(payload, dict):
        return []
    info = payload.get("info")
    if not isinstance(info, dict):
        return []

    snippets: list[RepositoryCheck] = []
    version = info.get("version")
    if isinstance(version, str) and version.strip():
        snippets.append(RepositoryCheck("latest version", "info", version.strip()))

    release_entries = payload.get("urls")
    if not isinstance(release_entries, list):
        releases = payload.get("releases")
        if isinstance(releases, dict) and isinstance(version, str) and version.strip():
            release_entries = releases.get(version.strip())

    timestamps: list[tuple[datetime, str]] = []
    for release_item in release_entries if isinstance(release_entries, list) else []:
        if not isinstance(release_item, dict):
            continue
        uploaded = release_item.get("upload_time_iso_8601") or release_item.get(
            "upload_time"
        )
        if not isinstance(uploaded, str) or not uploaded.strip():
            continue
        normalized = uploaded.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        timestamps.append((parsed, uploaded.strip()))
    if timestamps:
        _, latest_uploaded = max(timestamps, key=lambda item: item[0])
        snippets.append(RepositoryCheck("latest release date", "info", latest_uploaded))

    summary = info.get("summary")
    if isinstance(summary, str) and summary.strip():
        snippets.append(RepositoryCheck("summary", "info", summary.strip()))

    author = info.get("author")
    if isinstance(author, str) and author.strip():
        snippets.append(RepositoryCheck("author", "info", author.strip()))

    author_email = info.get("author_email")
    if isinstance(author_email, str) and author_email.strip():
        snippets.append(RepositoryCheck("author email", "info", author_email.strip()))

    requires_python = info.get("requires_python")
    if isinstance(requires_python, str) and requires_python.strip():
        snippets.append(
            RepositoryCheck("requires python", "info", requires_python.strip())
        )

    project_url = info.get("project_url") or info.get("home_page")
    if isinstance(project_url, str) and project_url.strip():
        snippets.append(RepositoryCheck("project url", "info", project_url.strip()))

    return snippets


def _normalized_project_name(name: str) -> str:
    return name.strip().lower().replace("_", "-").replace(".", "-")


def resolve_dist_dir(project_dir: Path, dist_dir: Path | None = None) -> Path:
    if dist_dir is None:
        return project_dir / DEFAULT_DIST_DIRNAME
    return dist_dir


def normalize_module_name(package_name: str) -> str:
    normalized = package_name.strip().replace("-", "_").replace(" ", "_")
    parts = [char if (char.isalnum() or char == "_") else "_" for char in normalized]
    module_name = "".join(parts).strip("_").lower()
    while "__" in module_name:
        module_name = module_name.replace("__", "_")
    if not module_name:
        raise PyPICommandError(
            "Package name must contain at least one valid letter or digit."
        )
    if module_name[0].isdigit():
        raise PyPICommandError("Module name cannot start with a digit.")
    return module_name


def _toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _py_string_literal(value: str) -> str:
    return json.dumps(value)


def _pascal_identifier(value: str) -> str:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", value) if part]
    if not parts:
        return "Config"
    return "".join(part[:1].upper() + part[1:].lower() for part in parts)


def _workflow_python_version(requires_python: str) -> str:
    match = re.search(r">=\s*(\d+\.\d+)", requires_python)
    if match:
        return match.group(1)
    return "3.10"


def _license_template_content(license_name: str, author: str | None) -> str:
    from datetime import date

    normalized = license_name.strip() or "MIT"
    template = LICENSE_TEMPLATES.get(normalized)
    if template is None:
        template = LICENSE_TEMPLATES["Proprietary"]
        if normalized.lower() not in {"proprietary", "unlicensed"}:
            return f"{normalized}\n\nCopyright (c) {date.today().year} {author or 'PROJECT OWNER'}.\n"
    return template.format(year=date.today().year, author=author or "PROJECT OWNER")


def _ensure_empty_or_missing(project_dir: Path) -> None:
    if not project_dir.exists():
        return
    if not project_dir.is_dir():
        raise PyPICommandError(
            f"Target path exists and is not a directory: {project_dir}"
        )
    if any(project_dir.iterdir()):
        raise PyPICommandError(f"Target directory is not empty: {project_dir}")


def _build_pyproject_content(
    package_name: str,
    module_name: str,
    description: str,
    requires_python: str,
    license_name: str,
    author: str | None,
    email: str | None,
) -> str:
    lines = [
        "[build-system]",
        'requires = ["setuptools>=61.0", "wheel"]',
        'build-backend = "setuptools.build_meta"',
        "",
        "[project]",
        f'name = "{_toml_escape(package_name)}"',
        'dynamic = ["version"]',
        f'description = "{_toml_escape(description)}"',
        'readme = "README.md"',
        f'requires-python = "{_toml_escape(requires_python)}"',
        f'license = "{_toml_escape(license_name)}"',
    ]
    if author and email:
        lines.append(
            f'authors = [{{name = "{_toml_escape(author)}", email = "{_toml_escape(email)}"}}]'
        )
    elif author:
        lines.append(f'authors = [{{name = "{_toml_escape(author)}"}}]')
    elif email:
        lines.append(f'authors = [{{email = "{_toml_escape(email)}"}}]')
    lines.extend(
        [
            f'keywords = ["{_toml_escape(module_name)}"]',
            "classifiers = [",
            '    "Programming Language :: Python :: 3",',
            '    "Operating System :: OS Independent",',
            "]",
            "",
            "[tool.setuptools.dynamic]",
            f'version = {{attr = "{module_name}.__version__"}}',
            "",
            "[tool.setuptools.packages.find]",
            'where = ["src"]',
            "",
            "[tool.setuptools]",
            "include-package-data = true",
            "",
        ]
    )
    return "\n".join(lines)


def _build_chatarch_pyproject_content(
    package_name: str,
    module_name: str,
    description: str,
    requires_python: str,
    license_name: str,
    author: str | None,
    email: str | None,
    include_mkdocs: bool = True,
    chatenv_provider_name: str | None = None,
) -> str:
    repo_slug = _chatarch_repo_slug(package_name)
    docs_url = _chatarch_docs_url(package_name)
    lines = [
        "[build-system]",
        'requires = ["setuptools>=61.0", "wheel"]',
        'build-backend = "setuptools.build_meta"',
        "",
        "[project]",
        f'name = "{_toml_escape(package_name)}"',
        'dynamic = ["version"]',
        f'description = "{_toml_escape(description)}"',
        'readme = "README.md"',
        f'requires-python = "{_toml_escape(requires_python)}"',
        f'license = "{_toml_escape(license_name)}"',
        'dependencies = ["click>=8.0", "chatstyle>=0.1.0,<0.2.0", "chatenv>=0.2.0,<0.3.0"]',
    ]
    if author and email:
        lines.append(
            f'authors = [{{name = "{_toml_escape(author)}", email = "{_toml_escape(email)}"}}]'
        )
    elif author:
        lines.append(f'authors = [{{name = "{_toml_escape(author)}"}}]')
    elif email:
        lines.append(f'authors = [{{email = "{_toml_escape(email)}"}}]')
    lines.extend(
        [
            f'keywords = ["{_toml_escape(module_name)}", "chatarch", "cli"]',
            "classifiers = [",
            '    "Programming Language :: Python :: 3",',
            '    "Operating System :: OS Independent",',
            "]",
            "",
            "[project.urls]",
            f'Homepage = "https://github.com/{_toml_escape(repo_slug)}"',
            f'Repository = "https://github.com/{_toml_escape(repo_slug)}"',
        ]
    )
    if include_mkdocs:
        lines.append(f'Documentation = "{_toml_escape(docs_url)}"')
    lines.extend(
        [
            "",
            "[project.scripts]",
            f'{module_name} = "{module_name}.cli:main"',
        ]
    )
    if chatenv_provider_name:
        lines.extend(
            [
                "",
                '[project.entry-points."chatenv.configs"]',
                f'{chatenv_provider_name} = "{module_name}.config"',
            ]
        )
    lines.extend(
        [
            "",
            "[project.optional-dependencies]",
            'dev = ["build", "pytest", "twine"]',
        ]
    )
    if include_mkdocs:
        lines.append('docs = ["mkdocs>=1.4.0", "mkdocs-material>=9.0.0", "mike>=2.0.0"]')
    lines.extend(
        [
            "",
            "[tool.setuptools.dynamic]",
            f'version = {{attr = "{module_name}.__version__"}}',
            "",
            "[tool.setuptools.packages.find]",
            'where = ["src"]',
            "",
            "[tool.setuptools]",
            "include-package-data = true",
            "",
        ]
    )
    return "\n".join(lines)


def _build_chatarch_chatenv_config_py(
    package_name: str,
    module_name: str,
    provider_name: str,
) -> str:
    class_name = f"{_pascal_identifier(module_name)}Config"
    storage_dir = _pascal_identifier(provider_name)
    env_key_prefix = module_name.upper()
    aliases = [provider_name]
    if module_name not in aliases:
        aliases.append(module_name)
    aliases_text = ", ".join(_py_string_literal(alias) for alias in aliases)
    env_key = f"{env_key_prefix}_API_KEY"
    return (
        textwrap.dedent(
            f'''\
            {_py_string_literal(f"Typed environment configuration for {package_name}.")}

            from chatenv import BaseEnvConfig, EnvField


            class {class_name}(BaseEnvConfig):
                {_py_string_literal(f"{package_name} ChatEnv configuration.")}

                _title = {_py_string_literal(f"{package_name} Configuration")}
                _aliases = [{aliases_text}]
                _storage_dir = {_py_string_literal(storage_dir)}

                {env_key_prefix}_API_KEY = EnvField(
                    {_py_string_literal(env_key)},
                    desc="API key",
                    is_sensitive=True,
                )


            __all__ = ["{class_name}"]
            '''
        ).strip()
        + "\n"
    )


def _chatarch_repo_slug(package_name: str) -> str:
    return f"ChatArch/{package_name}"


def _chatarch_docs_url(package_name: str) -> str:
    return f"https://ChatArch.github.io/{package_name}"


def _chatarch_badge_block(
    package_name: str, *, include_mkdocs: bool, include_workflows: bool
) -> str:
    repo_slug = _chatarch_repo_slug(package_name)
    docs_url = _chatarch_docs_url(package_name)
    lines = [
        '<div align="center">',
        f'    <a href="https://pypi.python.org/pypi/{package_name}">',
        f'        <img src="https://img.shields.io/pypi/v/{package_name}.svg" alt="PyPI version" />',
        "    </a>",
    ]
    if include_workflows:
        lines.extend(
            [
                f'    <a href="https://github.com/{repo_slug}/actions/workflows/ci.yml">',
                f'        <img src="https://github.com/{repo_slug}/actions/workflows/ci.yml/badge.svg" alt="Tests" />',
                "    </a>",
            ]
        )
    if include_mkdocs:
        lines.extend(
            [
                f'    <a href="{docs_url}">',
                '        <img src="https://img.shields.io/badge/docs-mkdocs-blue.svg" alt="Documentation" />',
                "    </a>",
            ]
        )
    lines.append("</div>")
    return "\n".join(lines)


def _chatarch_layout_lines(*, include_mkdocs: bool) -> str:
    lines = [
        "- `src/`：包源码",
        "- `tests/code-tests/`：代码测试和历史测试迁移",
        "- `tests/cli-tests/`：真实 CLI 测试，doc-first",
        "- `tests/mock-cli-tests/`：mock/fake CLI 测试，doc-first",
    ]
    if include_mkdocs:
        lines.append("- `docs/`：长期维护文档，由 mkdocs 构建")
    return "\n".join(lines)


def _chatarch_layout_lines_en(*, include_mkdocs: bool) -> str:
    lines = [
        "- `src/`: package source code",
        "- `tests/code-tests/`: code tests and migrated historical tests",
        "- `tests/cli-tests/`: real CLI tests, doc-first",
        "- `tests/mock-cli-tests/`: mock/fake CLI tests, doc-first",
    ]
    if include_mkdocs:
        lines.append("- `docs/`: long-lived project docs built by mkdocs")
    return "\n".join(lines)


def _build_chatarch_readme(
    package_name: str,
    module_name: str,
    description: str,
    *,
    include_mkdocs: bool = True,
    include_workflows: bool = True,
) -> str:
    badges = _chatarch_badge_block(
        package_name,
        include_mkdocs=include_mkdocs,
        include_workflows=include_workflows,
    )
    layout = _chatarch_layout_lines(include_mkdocs=include_mkdocs)
    return f"""\
{badges}

<div align="center">

[English](README.en.md) | [简体中文](README.md)
</div>

# {package_name}

{description}

## 快速开始

```bash
pip install -e ".[dev]"
{module_name} hello ChatArch
python -m pytest -q
python -m build
```

## CLI 规范

这个模板默认依赖 `chatstyle>=0.1.0,<0.2.0` 和 `chatenv>=0.2.0,<0.3.0`，新的命令应优先使用：

- `CommandSchema` / `CommandField` 描述输入。
- `add_interactive_option()` 提供统一 `-i/-I`。
- `resolve_command_inputs()` 统一缺参补问、默认值、TTY 与校验。

## 目录结构

{layout}

## 开发说明

扩展脚手架前，先阅读 `DEVELOP.md` 和 `AGENTS.md`。
"""


def _build_chatarch_readme_en(
    package_name: str,
    module_name: str,
    description: str,
    *,
    include_mkdocs: bool = True,
    include_workflows: bool = True,
) -> str:
    badges = _chatarch_badge_block(
        package_name,
        include_mkdocs=include_mkdocs,
        include_workflows=include_workflows,
    )
    layout = _chatarch_layout_lines_en(include_mkdocs=include_mkdocs)
    return f"""\
{badges}

<div align="center">

[English](README.en.md) | [简体中文](README.md)
</div>

# {package_name}

{description}

## Quick Start

```bash
pip install -e ".[dev]"
{module_name} hello ChatArch
python -m pytest -q
python -m build
```

## CLI Contract

This template depends on `chatstyle>=0.1.0,<0.2.0` and `chatenv>=0.2.0,<0.3.0`. New commands should prefer:

- `CommandSchema` / `CommandField` for inputs.
- `add_interactive_option()` for the shared `-i/-I` switch.
- `resolve_command_inputs()` for missing args, defaults, TTY behavior, and validation.

## Layout

{layout}

## Development Notes

See `DEVELOP.md` and `AGENTS.md` before expanding the scaffold.
"""


def _build_chatarch_develop_md() -> str:
    return (
        textwrap.dedent(
            """
            # Development Guide

            ## CLI Rules

            - Use `chatstyle>=0.1.0,<0.2.0` and `chatenv>=0.2.0,<0.3.0` as the canonical CLI interaction runtime.
            - Prefer `CommandSchema`, `CommandField`, `add_interactive_option()`, and `resolve_command_inputs()` for new commands.
            - Missing required args should auto-enter interactive mode when recoverable.
            - `-i` forces interactive mode; `-I` disables prompting and must fail fast.
            - Prompt defaults must match actual execution defaults.
            - Sensitive values must stay masked in prompts and summaries.
            - Prefer lazy imports in CLI wiring and keep implementation imports local when possible.

            ## Docs and Tests

            - Use doc-first CLI testing.
            - Put real CLI coverage under `tests/cli-tests/`.
            - Put mock/fake CLI coverage under `tests/mock-cli-tests/`.
            - Keep `README.md`, `docs/`, and `CHANGELOG.md` in sync with user-facing changes.

            ## Automation

            - Keep automation small and reviewable.
            - Prefer commands that can run in CI without interactive prompts.
            - Ensure generated defaults are safe for local development.
            """
        ).strip()
        + "\n"
    )


def _build_chatarch_changelog() -> str:
    return "# Changelog\n\n## YYYY-MM-DD\n\n### Added\n\n### Changed\n\n### Fixed\n"


def _build_chatarch_cli_py(module_name: str) -> str:
    return (
        textwrap.dedent(
            f"""
            \"\"\"CLI entrypoint for {module_name}.\"\"\"

            import click
            from chatstyle import (
                CommandField,
                CommandSchema,
                add_interactive_option,
                render_success,
                resolve_command_inputs,
            )


            HELLO_SCHEMA = CommandSchema(
                name="hello",
                fields=(CommandField("name", prompt="name", required=True),),
            )


            @click.group()
            def main() -> None:
                \"\"\"{module_name} command line interface.\"\"\"


            @main.command()
            @click.argument("name", required=False)
            @add_interactive_option
            def hello(name: str | None, interactive: bool | None) -> None:
                \"\"\"Print a greeting with ChatStyle-backed input resolution.\"\"\"

                values = resolve_command_inputs(
                    schema=HELLO_SCHEMA,
                    provided={{"name": name}},
                    interactive=interactive,
                    usage="Usage: {module_name} hello [NAME]",
                )
                render_success(f"Hello, {{values['name']}}!")


            if __name__ == "__main__":
                main()
            """
        ).strip()
        + "\n"
    )


def _build_chatarch_test_cli_py(module_name: str) -> str:
    return (
        textwrap.dedent(
            f"""
            from click.testing import CliRunner

            from {module_name}.cli import main


            def test_hello_command_accepts_explicit_name():
                result = CliRunner().invoke(main, ["hello", "ChatArch"])

                assert result.exit_code == 0
                assert "Hello, ChatArch!" in result.output
            """
        ).strip()
        + "\n"
    )


def _build_chatarch_docs_index(package_name: str) -> str:
    return (
        textwrap.dedent(
            f"""
            # {package_name} 文档

            这里收纳 `{package_name}` 的长期维护文档。

            ## 本地预览

            ```bash
            pip install -e ".[docs]"
            mkdocs serve
            ```

            英文版见：[index.en.md](index.en.md)。
            """
        ).strip()
        + "\n"
    )


def _build_chatarch_docs_index_en(package_name: str) -> str:
    return (
        textwrap.dedent(
            f"""
            # {package_name} Docs

            Long-lived documentation for `{package_name}` lives here.

            ## Local Preview

            ```bash
            pip install -e ".[docs]"
            mkdocs serve
            ```

            Chinese version: [index.md](index.md).
            """
        ).strip()
        + "\n"
    )


def _build_chatarch_mkdocs_yml(package_name: str) -> str:
    repo_slug = _chatarch_repo_slug(package_name)
    docs_url = _chatarch_docs_url(package_name)
    return (
        textwrap.dedent(
            f"""
            site_name: {package_name} 文档
            site_url: {docs_url}
            repo_url: https://github.com/{repo_slug}
            theme:
              name: material
              language: zh
            nav:
              - 首页: index.md
              - English: index.en.md
            """
        ).strip()
        + "\n"
    )


def _build_chatarch_agends_md() -> str:
    return (
        textwrap.dedent(
            """
            # Agent Notes

            ## Development Expectations

            - Keep changes minimal and reviewable.
            - Prefer doc-first CLI tests.
            - Sync docs and changelog with user-facing behavior.
            - Use interactive prompts only when arguments are missing and recoverable.
            """
        ).strip()
        + "\n"
    )


def scaffold_package(
    package_name: str,
    project_dir: Path,
    *,
    initial_version: str = "0.1.0",
    description: str | None = None,
    requires_python: str = ">=3.9",
    license_name: str = "MIT",
    author: str | None = None,
    email: str | None = None,
    template: str = "default",
    include_mkdocs: bool | None = None,
    include_workflows: bool | None = None,
    include_chatenv_provider: bool = False,
    chatenv_provider_name: str | None = None,
) -> ScaffoldResult:
    package_name = package_name.strip()
    if not package_name:
        raise PyPICommandError("Package name is required.")
    if template == "chatarch" and requires_python == ">=3.9":
        requires_python = ">=3.10"
    if include_mkdocs is None:
        include_mkdocs = template == "chatarch"
    if include_workflows is None:
        include_workflows = template == "chatarch"
    if chatenv_provider_name and not include_chatenv_provider:
        raise PyPICommandError(
            "chatenv_provider_name requires include_chatenv_provider=True."
        )
    if include_chatenv_provider and template != "chatarch":
        raise PyPICommandError(
            "include_chatenv_provider is only supported by the chatarch template."
        )

    module_name = normalize_module_name(package_name)
    resolved_chatenv_provider_name = (
        normalize_module_name(chatenv_provider_name or module_name)
        if include_chatenv_provider
        else None
    )
    workflow_python_version = _workflow_python_version(requires_python)
    project_dir = Path(project_dir)
    _ensure_empty_or_missing(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)

    description = description or f"{package_name} package"
    src_dir = project_dir / "src" / module_name
    tests_dir = project_dir / "tests"
    created_files: list[Path] = []

    src_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    file_map = {
        project_dir / "pyproject.toml": _build_pyproject_content(
            package_name=package_name,
            module_name=module_name,
            description=description,
            requires_python=requires_python,
            license_name=license_name,
            author=author,
            email=email,
        ),
        project_dir / "README.md": textwrap.dedent(f"""
            # {package_name}

            {description}

            ## Quick Start

            ```bash
            chattool pypi build --project-dir .
            chattool pypi check --project-dir .
            chattool pypi upload --project-dir .
            ```
        """).strip()
        + "\n",
        project_dir / "LICENSE": _license_template_content(license_name, author),
        project_dir / ".gitignore": textwrap.dedent("""
            __pycache__/
            .pytest_cache/
            .venv/
            build/
            dist/
            *.egg-info/
        """).strip()
        + "\n",
        src_dir / "__init__.py": textwrap.dedent(f'''
            """{package_name} package."""

            __all__ = ["__version__"]

            __version__ = "{initial_version}"
        ''').strip()
        + "\n",
        tests_dir / "conftest.py": textwrap.dedent("""
            from pathlib import Path
            import sys


            ROOT = Path(__file__).resolve().parents[1]
            SRC = ROOT / "src"
            if str(SRC) not in sys.path:
                sys.path.insert(0, str(SRC))
        """).strip()
        + "\n",
        tests_dir / "test_version.py": textwrap.dedent(f"""
            from {module_name} import __version__


            def test_version_present():
                assert __version__ == "{initial_version}"
        """).strip()
        + "\n",
    }

    if template == "chatarch":
        (tests_dir / "cli-tests").mkdir(parents=True, exist_ok=True)
        (tests_dir / "mock-cli-tests").mkdir(parents=True, exist_ok=True)
        (tests_dir / "code-tests").mkdir(parents=True, exist_ok=True)
        if include_mkdocs:
            (project_dir / "docs").mkdir(parents=True, exist_ok=True)
        if include_workflows:
            (project_dir / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
        file_map.update(
            {
                project_dir / "pyproject.toml": _build_chatarch_pyproject_content(
                    package_name=package_name,
                    module_name=module_name,
                    description=description,
                    requires_python=requires_python,
                    license_name=license_name,
                    author=author,
                    email=email,
                    include_mkdocs=include_mkdocs,
                    chatenv_provider_name=resolved_chatenv_provider_name,
                ),
                project_dir / "README.md": _build_chatarch_readme(
                    package_name,
                    module_name,
                    description,
                    include_mkdocs=include_mkdocs,
                    include_workflows=include_workflows,
                ),
                project_dir / "README.en.md": _build_chatarch_readme_en(
                    package_name,
                    module_name,
                    description,
                    include_mkdocs=include_mkdocs,
                    include_workflows=include_workflows,
                ),
                project_dir / "DEVELOP.md": _build_chatarch_develop_md(),
                project_dir / "CHANGELOG.md": _build_chatarch_changelog(),
                project_dir / "AGENTS.md": _build_chatarch_agends_md(),
                project_dir / "mkdocs.yml": _build_chatarch_mkdocs_yml(
                    package_name
                ),
                project_dir / "docs" / "index.md": _build_chatarch_docs_index(
                    package_name
                ),
                project_dir / "docs" / "index.en.md": _build_chatarch_docs_index_en(
                    package_name
                ),
                tests_dir
                / "cli-tests"
                / "README.md": "# CLI Tests\n\nReal CLI tests live here.\n",
                tests_dir
                / "mock-cli-tests"
                / "README.md": "# Mock CLI Tests\n\nMock/fake CLI tests live here.\n",
                tests_dir
                / "code-tests"
                / "README.md": "# Code Tests\n\nNon-CLI code tests live here.\n",
                src_dir / "cli.py": _build_chatarch_cli_py(module_name),
                tests_dir / "test_cli.py": _build_chatarch_test_cli_py(module_name),
                project_dir / ".github" / "workflows" / "ci.yml": textwrap.dedent(
                    """
                    name: CI

                    on:
                      push:
                        branches:
                          - main
                          - master
                      pull_request:

                    jobs:
                      test:
                        runs-on: ubuntu-latest
                        steps:
                          - uses: actions/checkout@v4
                          - name: Configure Git Credentials
                            run: |
                              git config user.name github-actions[bot]
                              git config user.email 41898282+github-actions[bot]@users.noreply.github.com
                          - uses: actions/setup-python@v5
                            with:
                              python-version: "{workflow_python_version}"
                          - run: python -m pip install --upgrade pip
                          - run: python -m pip install -e ".[dev,docs]"
                          - run: python -m pytest -q
                          - run: python -m build
                          - run: mkdocs build --strict
                    """
                )
                .replace("{workflow_python_version}", workflow_python_version)
                .strip()
                + "\n",
                project_dir / ".github" / "workflows" / "publish.yml": textwrap.dedent(
                    """
                    name: Publish Package

                    on:
                      push:
                        tags:
                          - "v*"
                      workflow_dispatch:

                    permissions:
                      contents: write
                      id-token: write

                    jobs:
                      publish:
                        runs-on: ubuntu-latest
                        environment: pypi
                        steps:
                          - uses: actions/checkout@v4
                            with:
                              fetch-depth: 0
                          - uses: actions/setup-python@v5
                            with:
                              python-version: "{workflow_python_version}"
                          - name: Resolve package version
                            id: meta
                            run: |
                              python - <<'PY'
                              import ast
                              import os
                              from pathlib import Path

                              module = ast.parse(Path("src/{module_name}/__init__.py").read_text(encoding="utf-8"))
                              for stmt in module.body:
                                  if not isinstance(stmt, ast.Assign):
                                      continue
                                  if any(isinstance(target, ast.Name) and target.id == "__version__" for target in stmt.targets):
                                      version = ast.literal_eval(stmt.value)
                                      break
                              else:
                                  raise SystemExit("__version__ not found in src/{module_name}/__init__.py")

                              with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
                                  print(f"version={version}", file=output)
                                  print(f"tag=v{version}", file=output)
                              PY
                          - name: Check tag matches package version
                            if: github.event_name == 'push'
                            env:
                              RELEASE_TAG: ${{ steps.meta.outputs.tag }}
                            run: |
                              if [ "${GITHUB_REF_NAME}" != "${RELEASE_TAG}" ]; then
                                echo "Tag ${GITHUB_REF_NAME} does not match package version ${RELEASE_TAG}."
                                exit 1
                              fi
                          - name: Check PyPI version
                            id: pypi
                            env:
                              PACKAGE_NAME: "{package_name}"
                              PACKAGE_VERSION: ${{ steps.meta.outputs.version }}
                            run: |
                              python - <<'PY'
                              import os
                              import urllib.error
                              import urllib.parse
                              import urllib.request

                              package = os.environ["PACKAGE_NAME"]
                              version = os.environ["PACKAGE_VERSION"]
                              url = f"https://pypi.org/pypi/{urllib.parse.quote(package)}/{urllib.parse.quote(version)}/json"
                              exists = "false"
                              try:
                                  urllib.request.urlopen(url, timeout=10)
                              except urllib.error.HTTPError as exc:
                                  if exc.code != 404:
                                      raise
                              else:
                                  exists = "true"

                              with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
                                  print(f"exists={exists}", file=output)
                              PY
                          - name: Stop when version is already on PyPI
                            if: steps.pypi.outputs.exists == 'true'
                            run: echo "{package_name} ${{ steps.meta.outputs.version }} is already on PyPI; skipping publish."
                          - name: Build distribution
                            if: steps.pypi.outputs.exists == 'false'
                            run: |
                              python -m pip install --upgrade pip build twine
                              python -m build
                              python -m twine check dist/*
                          - name: Publish to PyPI
                            if: steps.pypi.outputs.exists == 'false'
                            uses: pypa/gh-action-pypi-publish@release/v1
                    """
                )
                .replace("{workflow_python_version}", workflow_python_version)
                .replace("{package_name}", package_name)
                .replace("{module_name}", module_name)
                .strip()
                + "\n",
                project_dir / ".github" / "workflows" / "deploy.yaml": textwrap.dedent(
                    """
                    name: Deploy Docs

                    on:
                      push:
                        branches:
                          - main
                          - master

                    permissions:
                      contents: write

                    jobs:
                      deploy:
                        runs-on: ubuntu-latest
                        steps:
                          - uses: actions/checkout@v4
                          - uses: actions/setup-python@v5
                            with:
                              python-version: "{workflow_python_version}"
                          - run: python -m pip install --upgrade pip
                          - run: python -m pip install -e ".[docs]"
                          - run: mkdocs gh-deploy --force
                    """
                )
                .replace("{workflow_python_version}", workflow_python_version)
                .strip()
                + "\n",
                project_dir / ".github" / "workflows" / "preview.yaml": textwrap.dedent(
                    """
                    name: Preview Docs

                    on:
                      pull_request:
                        branches:
                          - main
                          - master

                    permissions:
                      contents: write
                      pull-requests: write

                    jobs:
                      deploy:
                        runs-on: ubuntu-latest
                        if: ${{ !github.event.pull_request.head.repo.fork }}
                        steps:
                          - uses: actions/checkout@v4
                          - name: Configure Git Credentials
                            run: |
                              git config user.name github-actions[bot]
                              git config user.email 41898282+github-actions[bot]@users.noreply.github.com
                          - uses: actions/setup-python@v5
                            with:
                              python-version: "{workflow_python_version}"
                          - run: python -m pip install --upgrade pip
                          - run: python -m pip install -e ".[docs]"
                          - run: |
                              git fetch origin
                              mike deploy dev -p --allow-empty
                              owner="${GITHUB_REPOSITORY_OWNER}"
                              repo="${GITHUB_REPOSITORY#*/}"
                              preview_url="https://${owner}.github.io/${repo}/dev/"
                              echo "Preview URL: ${preview_url}" >> "$GITHUB_STEP_SUMMARY"

                          - name: Comment PR with Preview Link
                            uses: actions/github-script@v6
                            with:
                              script: |
                                const { payload, repo } = context;
                                const previewLink = `https://${repo.owner}.github.io/${repo.repo}/dev/`;
                                const comments = await github.rest.issues.listComments({
                                  owner: repo.owner,
                                  repo: repo.repo,
                                  issue_number: payload.number,
                                });
                                const existingComment = comments.data.find(comment => comment.body.includes(previewLink));
                                if (!existingComment) {
                                  await github.rest.issues.createComment({
                                    owner: repo.owner,
                                    repo: repo.repo,
                                    issue_number: payload.number,
                                    body: `Preview available at: ${previewLink}`,
                                  });
                                }
                    """
                )
                .replace("{workflow_python_version}", workflow_python_version)
                .strip()
                + "\n",
            }
        )
        if resolved_chatenv_provider_name:
            file_map[src_dir / "config.py"] = _build_chatarch_chatenv_config_py(
                package_name=package_name,
                module_name=module_name,
                provider_name=resolved_chatenv_provider_name,
            )
        if not include_mkdocs:
            for optional_path in (
                project_dir / "mkdocs.yml",
                project_dir / "docs" / "index.md",
                project_dir / "docs" / "index.en.md",
                project_dir / ".github" / "workflows" / "deploy.yaml",
                project_dir / ".github" / "workflows" / "preview.yaml",
            ):
                file_map.pop(optional_path, None)
            ci_path = project_dir / ".github" / "workflows" / "ci.yml"
            if ci_path in file_map:
                file_map[ci_path] = file_map[ci_path].replace(
                    'python -m pip install -e ".[dev,docs]"',
                    'python -m pip install -e ".[dev]"',
                ).replace("\n                          - run: mkdocs build --strict", "")
        if not include_workflows:
            for optional_path in list(file_map):
                if ".github" in optional_path.parts:
                    file_map.pop(optional_path, None)

    for path, content in file_map.items():
        path.write_text(content, encoding="utf-8")
        created_files.append(path)

    return ScaffoldResult(
        project_dir=project_dir,
        package_name=package_name,
        module_name=module_name,
        created_files=sorted(created_files),
    )


def _load_pyproject(project_dir: Path) -> dict:
    pyproject_path = project_dir / "pyproject.toml"
    if not pyproject_path.exists():
        raise PyPICommandError(f"pyproject.toml not found under {project_dir}")
    try:
        return tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover
        raise PyPICommandError(f"Failed to parse {pyproject_path}: {exc}") from exc


def _extract_license_text(license_value) -> str | None:
    if isinstance(license_value, str):
        return license_value
    if isinstance(license_value, dict):
        if license_value.get("text"):
            return str(license_value["text"])
        if license_value.get("file"):
            return f"file:{license_value['file']}"
    return None


def _extract_readme_path(readme_value) -> str | None:
    if isinstance(readme_value, str):
        return readme_value
    if isinstance(readme_value, dict) and readme_value.get("file"):
        return str(readme_value["file"])
    return None


def _resolve_dynamic_version_source(
    pyproject: dict, dynamic_fields: list[str]
) -> str | None:
    if "version" not in dynamic_fields:
        return None
    tool_data = pyproject.get("tool", {})
    setuptools_data = (
        tool_data.get("setuptools", {}) if isinstance(tool_data, dict) else {}
    )
    dynamic_data = (
        setuptools_data.get("dynamic", {}) if isinstance(setuptools_data, dict) else {}
    )
    version_data = (
        dynamic_data.get("version") if isinstance(dynamic_data, dict) else None
    )
    if isinstance(version_data, dict):
        if version_data.get("attr"):
            return f"dynamic via attr={version_data['attr']}"
        if version_data.get("file"):
            return f"dynamic via file={version_data['file']}"
    return "dynamic"


def _load_attr_version(project_dir: Path, attr_path: str) -> str | None:
    module_path, _, attribute = attr_path.rpartition(".")
    if not module_path or not attribute:
        return None
    relative_parts = module_path.split(".")
    candidate_files = []
    for base_dir in (project_dir / "src", project_dir):
        candidate_files.append(base_dir.joinpath(*relative_parts, "__init__.py"))
        candidate_files.append(base_dir.joinpath(*relative_parts).with_suffix(".py"))

    for candidate in candidate_files:
        if not candidate.exists():
            continue
        try:
            spec = importlib.util.spec_from_file_location(
                f"_chattool_pypi_dynamic_{candidate.stem}_{abs(hash(candidate))}",
                candidate,
            )
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            value = getattr(module, attribute, None)
        except Exception:  # pragma: no cover
            continue
        if value is not None:
            return str(value)
    return None


def _load_file_version(project_dir: Path, relative_path: str) -> str | None:
    target = project_dir / relative_path
    if not target.exists():
        return None
    content = target.read_text(encoding="utf-8").strip()
    return content or None


def _resolve_dynamic_version_value(
    project_dir: Path, pyproject: dict, dynamic_fields: list[str]
) -> str | None:
    if "version" not in dynamic_fields:
        return None
    tool_data = pyproject.get("tool", {})
    setuptools_data = (
        tool_data.get("setuptools", {}) if isinstance(tool_data, dict) else {}
    )
    dynamic_data = (
        setuptools_data.get("dynamic", {}) if isinstance(setuptools_data, dict) else {}
    )
    version_data = (
        dynamic_data.get("version") if isinstance(dynamic_data, dict) else None
    )
    if isinstance(version_data, dict):
        attr_path = version_data.get("attr")
        if isinstance(attr_path, str):
            return _load_attr_version(project_dir, attr_path)
        file_path = version_data.get("file")
        if isinstance(file_path, str):
            return _load_file_version(project_dir, file_path)
    return None


def read_project_metadata(project_dir: Path) -> ProjectMetadata:
    pyproject = _load_pyproject(project_dir)
    project_data = pyproject.get("project")
    if not isinstance(project_data, dict):
        raise PyPICommandError("Missing [project] table in pyproject.toml")

    dynamic_fields = [
        field for field in project_data.get("dynamic", []) if isinstance(field, str)
    ]
    version = project_data.get("version")
    version_source = None
    if not version:
        version_source = _resolve_dynamic_version_source(pyproject, dynamic_fields)
        version = _resolve_dynamic_version_value(project_dir, pyproject, dynamic_fields)

    return ProjectMetadata(
        name=project_data.get("name"),
        version=version if isinstance(version, str) else None,
        version_source=version_source,
        readme=_extract_readme_path(project_data.get("readme")),
        requires_python=project_data.get("requires-python"),
        license_text=_extract_license_text(project_data.get("license")),
        dynamic_fields=dynamic_fields,
    )


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _find_license_file(project_dir: Path) -> Path | None:
    for candidate in ("LICENSE", "LICENSE.txt", "LICENSE.md"):
        path = project_dir / candidate
        if path.exists():
            return path
    return None


def collect_doctor_checks(
    project_dir: Path, dist_dir: Path | None = None
) -> list[DoctorCheck]:
    project_dir = Path(project_dir)
    dist_dir = resolve_dist_dir(project_dir, dist_dir)
    pyproject_path = project_dir / "pyproject.toml"

    checks: list[DoctorCheck] = []
    if not pyproject_path.exists():
        return [
            DoctorCheck(
                label="pyproject.toml",
                status="fail",
                detail=f"missing: {pyproject_path}",
                hint="Create pyproject.toml before using chattool pypi.",
            )
        ]

    checks.append(DoctorCheck("pyproject.toml", "ok", f"found: {pyproject_path.name}"))

    try:
        metadata = read_project_metadata(project_dir)
    except PyPICommandError as exc:
        checks.append(DoctorCheck("project metadata", "fail", str(exc)))
        return checks

    checks.append(
        DoctorCheck(
            "project.name",
            "ok" if metadata.name else "fail",
            metadata.name or "missing [project].name",
        )
    )
    if metadata.version:
        version_detail = metadata.version
        if metadata.version_source:
            version_detail = f"{metadata.version} ({metadata.version_source})"
        status = "ok"
    elif metadata.version_source:
        version_detail = metadata.version_source
        status = "ok"
    else:
        version_detail = "missing version or dynamic version configuration"
        status = "fail"
    checks.append(DoctorCheck("project.version", status, version_detail))
    checks.append(
        DoctorCheck(
            "project.readme",
            "ok" if metadata.readme else "fail",
            metadata.readme or "missing [project].readme",
        )
    )
    checks.append(
        DoctorCheck(
            "project.requires-python",
            "ok" if metadata.requires_python else "fail",
            metadata.requires_python or "missing [project].requires-python",
        )
    )
    checks.append(
        DoctorCheck(
            "project.license",
            "ok" if metadata.license_text else "fail",
            metadata.license_text or "missing [project].license",
        )
    )

    if metadata.readme:
        readme_path = project_dir / metadata.readme
        checks.append(
            DoctorCheck(
                "README file",
                "ok" if readme_path.exists() else "fail",
                str(readme_path.relative_to(project_dir))
                if readme_path.exists()
                else f"missing: {metadata.readme}",
            )
        )

    license_path = _find_license_file(project_dir)
    build_available = _module_available("build")
    twine_available = _module_available("twine")

    checks.append(
        DoctorCheck(
            "LICENSE file",
            "ok" if license_path else "fail",
            license_path.name
            if license_path
            else "missing LICENSE / LICENSE.txt / LICENSE.md",
        )
    )
    checks.append(
        DoctorCheck(
            "build module",
            "ok" if build_available else "fail",
            "installed" if build_available else "python -m build unavailable",
            hint='Install with `pip install build` or `pip install "chattool[pypi]"`.',
        )
    )
    checks.append(
        DoctorCheck(
            "twine module",
            "ok" if twine_available else "fail",
            "installed" if twine_available else "python -m twine unavailable",
            hint='Install with `pip install twine` or `pip install "chattool[pypi]"`.',
        )
    )

    existing_artifacts = find_distributions(dist_dir)
    if existing_artifacts:
        checks.append(
            DoctorCheck(
                "dist artifacts",
                "warn",
                f"{len(existing_artifacts)} existing file(s) under {dist_dir}",
                hint="Use `chattool pypi build --clean` to replace old build artifacts.",
            )
        )
    else:
        checks.append(
            DoctorCheck(
                "dist artifacts", "ok", f"no existing artifacts under {dist_dir}"
            )
        )
    return checks


def doctor_has_failures(checks: list[DoctorCheck]) -> bool:
    return any(check.status == "fail" for check in checks)


def find_distributions(dist_dir: Path) -> list[Path]:
    dist_dir = Path(dist_dir)
    if not dist_dir.exists():
        return []
    found: list[Path] = []
    for pattern in ("*.whl", "*.tar.gz", "*.zip"):
        found.extend(dist_dir.glob(pattern))
    return sorted(set(path.resolve() for path in found))


def _repository_json_base(repository: str, repository_url: str | None = None) -> str:
    if repository_url:
        parsed = urllib_parse.urlparse(repository_url)
        host = parsed.netloc.lower()
        if host == "upload.pypi.org":
            return "https://pypi.org"
        if host == "test.pypi.org":
            return "https://test.pypi.org"
        return f"{parsed.scheme}://{parsed.netloc}"
    if repository == "pypi":
        return "https://pypi.org"
    return "https://test.pypi.org"


def _fetch_repository_json(url: str, timeout: float = 5.0) -> tuple[int, dict | None]:
    request = urllib_request.Request(
        url,
        headers={"Accept": "application/json"},
    )
    try:
        with urllib_request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
            return response.status, json.loads(payload)
    except urllib_error.HTTPError as exc:
        if exc.code == 404:
            return 404, None
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise PyPICommandError(
            f"Repository query failed for {url}: HTTP {exc.code} {detail or exc.reason}"
        ) from exc
    except urllib_error.URLError as exc:
        raise PyPICommandError(
            f"Repository query failed for {url}: {exc.reason}"
        ) from exc
    except TimeoutError as exc:
        raise PyPICommandError(f"Repository query failed for {url}: timeout") from exc
    except json.JSONDecodeError as exc:
        raise PyPICommandError(
            f"Repository query returned invalid JSON for {url}: {exc}"
        ) from exc


def check_repository_conflicts(
    package_name: str,
    *,
    repository: str = "pypi",
    repository_url: str | None = None,
    timeout: float = 5.0,
    fetcher=_fetch_repository_json,
) -> list[RepositoryCheck]:
    package_name = package_name.strip()
    if not package_name:
        raise PyPICommandError(
            "Package name is required for repository conflict checks."
        )

    base_url = _repository_json_base(repository, repository_url)
    package_url = f"{base_url}/pypi/{urllib_parse.quote(package_name)}/json"
    package_status, payload = fetcher(package_url, timeout=timeout)
    target_label = repository_url or repository

    checks: list[RepositoryCheck] = []
    if package_status == 404:
        return [
            RepositoryCheck(
                label="package name",
                status="ok",
                detail=f"{package_name} is available on {target_label}",
                hint="Exact project-name check. This does not use PyPI search results.",
            ),
            RepositoryCheck(
                label="result",
                status="ok",
                detail=f"name is available on {target_label}",
                hint="Use this as a first-pass name check before publishing.",
            ),
        ]
    else:
        checks.append(
            RepositoryCheck(
                label="package name",
                status="fail",
                detail=f"{package_name} already exists on {target_label}",
                hint="Choose another package name for a new package. Only keep this name if you own the existing project.",
            )
        )
        checks.append(
            RepositoryCheck(
                label="result",
                status="fail",
                detail=f"blocked for a new package: {package_name} already exists on {target_label}",
                hint="Choose another package name unless you own the existing project.",
            )
        )
        checks.extend(_extract_project_snippets(payload))
    return checks


def _clean_dist_dir(dist_dir: Path) -> None:
    if not dist_dir.exists():
        return
    for path in dist_dir.iterdir():
        if path.is_file() or path.is_symlink():
            path.unlink()


def run_command(
    args: list[str], cwd: Path, env: dict[str, str] | None = None
) -> CommandResult:
    process = subprocess.run(
        args,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(
        args=list(args),
        returncode=process.returncode,
        stdout=process.stdout,
        stderr=process.stderr,
    )


def _ensure_success(result: CommandResult, action: str) -> CommandResult:
    if result.returncode == 0:
        return result
    detail = result.stderr.strip() or result.stdout.strip() or "no output"
    raise PyPICommandError(f"{action} failed: {detail}")


def build_package(
    project_dir: Path,
    dist_dir: Path | None = None,
    *,
    clean: bool = True,
    sdist: bool = False,
    wheel: bool = False,
    runner=run_command,
) -> tuple[CommandResult, list[Path]]:
    project_dir = Path(project_dir)
    dist_dir = resolve_dist_dir(project_dir, dist_dir)
    if not (project_dir / "pyproject.toml").exists():
        raise PyPICommandError(f"pyproject.toml not found under {project_dir}")

    if clean:
        _clean_dist_dir(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)

    args = [sys.executable, "-m", "build", "--outdir", str(dist_dir)]
    if sdist and not wheel:
        args.append("--sdist")
    elif wheel and not sdist:
        args.append("--wheel")

    result = _ensure_success(runner(args, project_dir), "Build")
    files = find_distributions(dist_dir)
    if not files:
        raise PyPICommandError(
            f"Build completed but no distributions were found under {dist_dir}"
        )
    return result, files


def check_distributions(
    project_dir: Path,
    dist_dir: Path | None = None,
    *,
    strict: bool = False,
    runner=run_command,
) -> tuple[CommandResult, list[Path]]:
    project_dir = Path(project_dir)
    dist_dir = resolve_dist_dir(project_dir, dist_dir)
    files = find_distributions(dist_dir)
    if not files:
        raise PyPICommandError(
            f"No distributions found under {dist_dir}. Run `chattool pypi build` first."
        )

    args = [sys.executable, "-m", "twine", "check"]
    if strict:
        args.append("--strict")
    args.extend(str(path) for path in files)
    result = _ensure_success(runner(args, project_dir), "Twine check")
    return result, files


def upload_distributions(
    project_dir: Path,
    dist_dir: Path | None = None,
    *,
    skip_existing: bool = False,
    runner=run_command,
) -> tuple[CommandResult, list[Path]]:
    project_dir = Path(project_dir)
    dist_dir = resolve_dist_dir(project_dir, dist_dir)
    files = find_distributions(dist_dir)
    if not files:
        raise PyPICommandError(
            f"No distributions found under {dist_dir}. Run `chattool pypi build` first."
        )

    args = [sys.executable, "-m", "twine", "upload"]
    if skip_existing:
        args.append("--skip-existing")
    args.extend(str(path) for path in files)
    result = _ensure_success(runner(args, project_dir), "Twine upload")
    return result, files
