import io
import json
from ftplib import FTP, error_perm, error_temp


class FTPManager:
    def __init__(self, host: str, port: int, user: str, password: str, server_json_path: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.server_json_path = server_json_path  # e.g. "R5/ServerDescription.json"

    def _connect(self) -> FTP:
        host = self.host.strip()
        port = self.port
        # If user accidentally put "host:port" in the host field, split it out
        if ":" in host:
            parts = host.rsplit(":", 1)
            host = parts[0]
            try:
                port = int(parts[1])
            except ValueError:
                pass
        ftp = FTP()
        ftp.connect(host, port, timeout=10)
        ftp.login(self.user, self.password)
        ftp.set_pasv(True)
        return ftp

    def test_connection(self) -> tuple[bool, str]:
        try:
            ftp = self._connect()
            ftp.quit()
            return True, "Connected successfully."
        except Exception as e:
            return False, str(e)

    def download_server_config(self) -> dict:
        ftp = self._connect()
        try:
            buf = io.BytesIO()
            ftp.retrbinary(f"RETR {self.server_json_path}", buf.write)
            buf.seek(0)
            return json.loads(buf.read().decode("utf-8"))
        finally:
            try:
                ftp.quit()
            except Exception:
                pass

    def upload_server_config(self, data: dict) -> None:
        ftp = self._connect()
        try:
            content = json.dumps(data, indent=2).encode("utf-8")
            buf = io.BytesIO(content)
            ftp.storbinary(f"STOR {self.server_json_path}", buf)
        finally:
            try:
                ftp.quit()
            except Exception:
                pass

    def _ensure_remote_dir(self, ftp: FTP, remote_dir: str) -> None:
        parts = remote_dir.replace("\\", "/").split("/")
        current = ""
        for part in parts:
            if not part:
                continue
            current = f"{current}/{part}" if current else part
            try:
                ftp.mkd(current)
            except error_perm:
                pass  # already exists

    def upload_pak(self, local_path, remote_mods_dir: str) -> None:
        import os
        ftp = self._connect()
        try:
            self._ensure_remote_dir(ftp, remote_mods_dir)
            remote_path = f"{remote_mods_dir.rstrip('/')}/{os.path.basename(str(local_path))}"
            with open(local_path, "rb") as f:
                ftp.storbinary(f"STOR {remote_path}", f)
        finally:
            try:
                ftp.quit()
            except Exception:
                pass

    def list_remote_mods(self, remote_mods_dir: str) -> list[str]:
        ftp = self._connect()
        try:
            try:
                return ftp.nlst(remote_mods_dir)
            except error_perm:
                return []
        finally:
            try:
                ftp.quit()
            except Exception:
                pass
