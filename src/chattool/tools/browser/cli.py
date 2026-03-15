import click


@click.group()
def cli():
    """Browser helpers."""
    pass


@cli.command(name="xhs-qrcode")
@click.option("--backend", default=None, help="Backend override (playwright|selenium|chromium).")
@click.option("-o", "--output", "output_path", default=None, help="Optional output image path.")
@click.option("-d", "--debug", "debug_enabled", is_flag=True, help="Enable debug artifacts under /tmp/chattool_xhs_debug.")
@click.option("--debug-dir", "debug_dir", default=None, help="Override debug directory path.")
@click.option("-t", "--timeout", default=15000, show_default=True, help="Timeout in ms.")
def xhs_qrcode(backend, output_path, debug_enabled, debug_dir, timeout):
    """Capture XHS login QR code via configured backend."""
    from chattool.tools.browser.xhs_qrcode import run_xhs_qr_capture

    run_xhs_qr_capture(
        backend=backend,
        output_path=output_path,
        timeout_ms=timeout,
        debug_enabled=debug_enabled,
        debug_dir=debug_dir,
    )
