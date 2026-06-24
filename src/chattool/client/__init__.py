from chattool.interaction import install_cli_warning_filters

install_cli_warning_filters()


def main_cli():
    from .main import cli

    cli()


def main_skill_cli():
    import sys

    from chattool.skill.cli import skill_cli

    skill_cli.main(args=sys.argv[1:], prog_name="chatskill")


__all__ = [
    "main_cli",
    "main_skill_cli",
]
