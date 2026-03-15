import os
import re
import shutil
import subprocess
import zipfile
import io
import stat
from pathlib import Path
import click
from chattool.setup.interactive import abort_if_force_without_tty, resolve_interactive_mode
from chattool.utils.custom_logger import setup_logger

logger = setup_logger("setup_chrome")

def get_chrome_version():
    """Detect installed Chrome version."""
    try:
        # Try common chrome executables
        for cmd in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]:
            if shutil.which(cmd):
                result = subprocess.run([cmd, "--version"], capture_output=True, text=True, check=True)
                # Output example: "Google Chrome 141.0.7390.54 "
                version_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", result.stdout)
                if version_match:
                    return version_match.group(1)
    except Exception as e:
        logger.error(f"Failed to detect Chrome version: {e}")
    return None

def get_chromedriver_url(version):
    """Get the download URL for the matching Chromedriver."""
    import httpx
    major_version = version.split('.')[0]
    
    # For older versions (< 115), use the old repository
    if int(major_version) < 115:
        try:
            # First get the specific latest release for this version
            # This is the user requested method
            release_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}"
            resp = httpx.get(release_url)
            if resp.status_code == 200:
                driver_version = resp.text.strip()
                return f"https://chromedriver.storage.googleapis.com/{driver_version}/chromedriver_linux64.zip"
        except Exception as e:
            logger.warning(f"Failed to check old repository: {e}")

    # For newer versions (>= 115) or if old method failed
    try:
        # Check known good versions for newer Chrome
        json_url = "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json"
        resp = httpx.get(json_url)
        if resp.status_code == 200:
            data = resp.json()
            milestones = data.get("milestones", {})
            if major_version in milestones:
                downloads = milestones[major_version].get("downloads", {})
                chromedriver = downloads.get("chromedriver", [])
                for item in chromedriver:
                    if item.get("platform") == "linux64":
                        return item.get("url")
            else:
                logger.warning(f"Major version {major_version} not found in milestones.")
    except Exception as e:
        logger.error(f"Failed to find driver in new repository: {e}")
        
    return None

def install_chromedriver(url, target_dir):
    """Download and install Chromedriver."""
    import httpx
    try:
        click.echo(f"Downloading Chromedriver from {url}...")
        resp = httpx.get(url, follow_redirects=True)
        resp.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            # Find the chromedriver binary in the zip
            # It might be in a subdirectory like 'chromedriver-linux64/chromedriver'
            driver_info = None
            for info in z.infolist():
                if info.is_dir():
                    continue
                if Path(info.filename).name == "chromedriver":
                    driver_info = info
                    break
            
            if not driver_info:
                raise Exception("chromedriver executable not found in archive")
                
            target_path = Path(target_dir) / "chromedriver"
            with z.open(driver_info) as source, open(target_path, "wb") as target:
                shutil.copyfileobj(source, target)
            
            # Make executable
            st = os.stat(target_path)
            os.chmod(target_path, st.st_mode | stat.S_IEXEC)
            try:
                subprocess.run([str(target_path), "--version"], capture_output=True, text=True, check=True)
            except Exception:
                raise Exception("Downloaded file is not a valid chromedriver binary")
            click.echo(f"Chromedriver installed to {target_path}")
            
    except Exception as e:
        click.echo(f"Failed to install chromedriver: {e}", err=True)
        raise

def setup_chrome_driver(interactive=None):
    """Main setup function."""
    usage = "Usage: chattool setup chrome [-i|-I]"
    interactive, can_prompt, force_interactive, _, need_prompt = resolve_interactive_mode(
        interactive=interactive,
        auto_prompt_condition=False,
    )
    abort_if_force_without_tty(force_interactive, can_prompt, usage)

    # Check if chromedriver is already installed
    existing_path = shutil.which("chromedriver")
    if existing_path:
        click.echo(f"Chromedriver is already installed at {existing_path}")
        if not need_prompt:
            click.echo("Updating existing installation...")
            target_dir = Path(existing_path).parent
        else:
            if not click.confirm("Do you want to update/reinstall?", default=True):
                return
            target_dir = Path(existing_path).parent
    else:
        target_dir = Path.home() / ".local" / "bin"

    version = get_chrome_version()
    if not version:
        click.echo("Could not detect Google Chrome version.", err=True)
        click.echo("Please install Google Chrome first:")
        click.echo("  wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb")
        click.echo("  sudo apt install ./google-chrome-stable_current_amd64.deb")
        return
        
    click.echo(f"Detected Chrome version: {version}")
    
    url = get_chromedriver_url(version)
    if not url:
        click.echo(f"Could not find matching Chromedriver for version {version}", err=True)
        return
        
    if need_prompt:
        target_dir = click.prompt(
            "Install directory", 
            default=str(target_dir), 
            type=click.Path(file_okay=False, dir_okay=True, writable=True)
        )
    
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    
    install_chromedriver(url, target_dir)
