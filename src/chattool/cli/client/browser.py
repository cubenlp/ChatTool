import click


@click.group()
def cli():
    """Browser helpers."""
    pass


@cli.command(name="xhs-qrcode")
@click.option("-o", "--output", "output_path", default=None, help="Output image path.")
@click.option("-d", "--debug", "debug_enabled", is_flag=True, help="Enable debug artifacts.")
@click.option("--debug-dir", "debug_dir", default=None, help="Debug directory path.")
@click.option("-t", "--timeout", default=15000, show_default=True, help="Timeout in ms.")
def xhs_qrcode(output_path, debug_enabled, debug_dir, timeout):
    """Capture XHS login QR code."""
    from chattool.tools.browser.xhs_qrcode import run_xhs_qr_capture

    run_xhs_qr_capture(
        output_path=output_path,
        timeout_ms=timeout,
        debug_enabled=debug_enabled,
        debug_dir=debug_dir,
    )
