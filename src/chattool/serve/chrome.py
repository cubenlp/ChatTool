import click
import subprocess
import sys
import shutil

@click.command()
@click.option('--driver', is_flag=True, help='Launch chromedriver')
@click.option('--cdp', is_flag=True, help='Launch google-chrome with remote debugging')
@click.option('--port', type=int, default=None, help='Port to listen on (driver default: 9515, cdp default: 9222)')
@click.option('--allowed-ips', default='127.0.0.1', help='Allowed IPs for chromedriver (default: 127.0.0.1)')
@click.option('--user-data-dir', default='/tmp/chrome-profile', help='User data directory for google-chrome (default: /tmp/chrome-profile)')
@click.option('--headless', is_flag=True, help='Run in headless mode')
def serve_chrome(driver, cdp, port, allowed_ips, user_data_dir, headless):
    """Serve Chrome or Chromedriver."""
    if driver and cdp:
        click.echo("Error: Cannot specify both --driver and --cdp")
        sys.exit(1)

    if not driver and not cdp:
        driver = True

    if port is None:
        port = 9515 if driver else 9222

    if driver:
        if not shutil.which('chromedriver'):
            click.echo("Error: chromedriver not found in PATH")
            click.echo("Run: chattool setup chrome")
            sys.exit(1)
        cmd = [
            'chromedriver',
            f'--port={port}',
            f'--allowed-ips={allowed_ips}'
        ]
        click.echo(f"Starting chromedriver: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            click.echo(f"chromedriver exited with code {e.returncode}")
            sys.exit(1)
        except KeyboardInterrupt:
            click.echo("\nStopping chromedriver...")

    if cdp:
        if not shutil.which('google-chrome'):
            click.echo("Error: google-chrome not found in PATH")
            click.echo("Install command:")
            click.echo("  wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb")
            click.echo("  sudo apt install ./google-chrome-stable_current_amd64.deb")
            sys.exit(1)
        cmd = [
            'google-chrome',
            f'--remote-debugging-port={port}',
            f'--user-data-dir={user_data_dir}'
        ]
        if headless:
            cmd.append('--headless')
            
        click.echo(f"Starting google-chrome: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            click.echo(f"google-chrome exited with code {e.returncode}")
            sys.exit(1)
        except KeyboardInterrupt:
            click.echo("\nStopping google-chrome...")
