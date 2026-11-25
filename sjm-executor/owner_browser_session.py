"""Local, owner-operated persistent sessions for SJM Control 360.
Never exports cookies, credentials or storage state. No automatic submit.
"""
import argparse
import os
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

SITES = {
    "ypai": ("https://freelancer.ypai.ai/work/login",
             "https://freelancer.ypai.ai/work/dashboard"),
}

def session_directory(site):
    if site not in SITES:
        raise ValueError("unregistered_site")
    root = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "SJM-Control360"
    for directory in (root, root / "owner-sessions", root / "owner-sessions" / site):
        if directory.is_symlink():
            raise ValueError("symlink_not_allowed")
        directory.mkdir(mode=0o700, exist_ok=True)
        if os.name == "posix":
            if directory.stat().st_uid != os.getuid():
                raise ValueError("profile_owner_mismatch")
            directory.chmod(0o700)
    return directory

def classify_page(site, url, status=None):
    login, dashboard = SITES[site]
    seen, expected = urlsplit(url), urlsplit(dashboard)
    if seen.scheme != "https" or seen.netloc != expected.netloc:
        return "unknown_or_external_login"
    if status in (401, 403) or seen.path.rstrip("/") == urlsplit(login).path:
        return "reconnect_required"
    if seen.path.rstrip("/") == expected.path and status == 200:
        return "dashboard_visible_unverified"
    return "session_not_verified"

def run_owner_browser(site, reconnect=False):
    login, dashboard = SITES[site]
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(session_directory(site)), headless=False,
            accept_downloads=False, ignore_https_errors=False, permissions=[])
        try:
            page = context.pages[0] if context.pages else context.new_page()
            response = page.goto(login if reconnect else dashboard,
                                 wait_until="domcontentloaded", timeout=20000)
            print(classify_page(site, page.url, response.status if response else None))
            print("Autentíquese personalmente si hace falta. Pulse Enter al terminar.")
            input()
        finally:
            context.close()
    print("Perfil local conservado. La autenticación real requiere comprobación.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("site", choices=sorted(SITES))
    parser.add_argument("--reconnect", action="store_true")
    args = parser.parse_args()
    run_owner_browser(args.site, args.reconnect)
