import json
import urllib.parse
import urllib.request
import re
from typing import Optional, Dict, Any, List

from chattool.utils.httpclient import HTTPClient
from chattool.config import TPLinkConfig

class TPLogin(HTTPClient):
    DEFAULT_AUTH_KEY = "RDpbLfCPsJZ7fiv"
    DEFAULT_AUTH_DICTIONARY = "yLwVl0zKqws7LgKPRQ84Mdt708T1qQ3Ha7xv3H7NyU84p21BriUWBU43odz3iP4rBL3cD02KZciXTysVXiV8ngg6vL48rPJyAUw0HurW20xqxv9aYb4M9wK1Ae0wlro510qXeU07kV57fQMc8L6aLgMLwygtc0F10a0Dg70TOoouyFhdysuRMO51yY5ZlOZZLEal1h0t9YQW0Ko7oBwmCAHoic4HYbUyVeU3sfQ1xtXcPcf1aT303wAQhv66qzW"

    def __init__(
        self,
        url: str = None,
        password: str = None,
        auth_key: str = None,
        auth_dictionary: str = None,
    ):
        self.url = url or TPLinkConfig.TPLOGIN_URL.value
        self.password = password or TPLinkConfig.TPLOGIN_AUTH_PASSWORD.value
        self.auth_key = auth_key
        self.auth_dictionary = auth_dictionary

        if not self.url:
            raise ValueError("TPLOGIN_URL not set")
        
        super().__init__(api_base=self.url)
        self.stok = None

    def _fetch_auth_params(self) -> bool:
        try:
            url_path = "/web-static/dynaform/class.js"
            full_url = f"{self.url.rstrip('/')}{url_path}"
            self.logger.info(f"Fetching auth params from {full_url}...")
            req = urllib.request.Request(
                full_url, 
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                content = response.read().decode("utf-8", errors="ignore")

            patterns = [
                r'orgAuthPwd=function\(\w+\)\{return this\.securityEncode\(\w+,\s*"([^"]+)"\s*,\s*"([^"]+)"\)\}',
                r'securityEncode\s*\([^,]+,\s*"([^"]+)"\s*,\s*"([^"]+)"'
            ]

            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    self.auth_key = match.group(1)
                    self.auth_dictionary = match.group(2)
                    self.logger.info("Successfully fetched auth params from router")
                    return True

            self.logger.warning("Could not find auth params in class.js")
            return False
                
        except Exception as e:
            self.logger.error(f"Error fetching auth params: {e}")
            return False

    def _security_encode(self, key: str, password: str, dictionary: str) -> str:
        result = ""
        key_len = len(key)
        pwd_len = len(password)
        dict_len = len(dictionary)
        
        max_len = max(key_len, pwd_len)
        
        for p in range(max_len):
            l = 187
            n = 187
            
            if p >= key_len:
                n = ord(password[p])
            elif p >= pwd_len:
                l = ord(key[p])
            else:
                l = ord(key[p])
                n = ord(password[p])
                
            index = (l ^ n) % dict_len
            result += dictionary[index]
            
        return result

    def _org_auth_pwd(self, password: str) -> str:
        if not self.auth_key or not self.auth_dictionary:
            self._fetch_auth_params()
            
        if not self.auth_key or not self.auth_dictionary:
            self.auth_key = self.DEFAULT_AUTH_KEY
            self.auth_dictionary = self.DEFAULT_AUTH_DICTIONARY
             
        return self._security_encode(self.auth_key, password, self.auth_dictionary)

    def _request_json_with_urllib(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        full_url = url if url.startswith(("http://", "https://")) else f"{self.url.rstrip('/')}/{url.lstrip('/')}"
        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }
        req = urllib.request.Request(full_url, data=data_bytes, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))

    def _request_json(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.post(url, data=payload).json()
        except Exception as e_httpx:
            try:
                return self._request_json_with_urllib(url, payload)
            except Exception as e_urllib:
                self.logger.error(f"Request failed by httpx and urllib: {e_httpx}; {e_urllib}")
                raise e_urllib

    def login(self) -> Optional[str]:
        if not self.password:
            self.logger.error("Password not set")
            return None
            
        encrypted_pwd = self._org_auth_pwd(self.password)
        
        payload = {
            "method": "do",
            "login": {
                "password": encrypted_pwd
            }
        }
        
        try:
            response_data = self._request_json("/", payload)
            if response_data.get("error_code") == 0:
                stok = response_data.get("stok")
                self.stok = urllib.parse.unquote(stok)
                self.logger.info(f"Login successful")
                return self.stok
            else:
                self.logger.error(f"Login failed: {response_data}")
                return None
        except Exception as e:
            self.logger.error(f"Error during login: {e}")
            return None

    def get_stok(self) -> Optional[str]:
        if not self.stok:
            self.login()
        return self.stok

    def _ds_request(self, method: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        stok = self.get_stok()
        if not stok:
            return None

        url_path = f"/stok={urllib.parse.quote(stok)}/ds"
        body = {"method": method}
        body.update(payload)

        try:
            response_data = self._request_json(url_path, body)
            if response_data.get("error_code") == 0:
                return response_data
            else:
                self.logger.error(f"API request failed: {response_data}")
                return None
        except Exception as e:
            self.logger.error(f"Error during API request: {e}")
            return None

    def get_device_info(self) -> Optional[Dict[str, Any]]:
        return self._ds_request("get", {"device_info": {"name": "info"}})

    def list_virtual_servers_raw(self) -> List[Dict[str, Any]]:
        data = self._ds_request("get", {"firewall": {"table": "redirect"}})
        if not data:
            return []
        return data.get("firewall", {}).get("redirect", [])

    def list_virtual_servers(self) -> List[Dict[str, Any]]:
        rules: List[Dict[str, Any]] = []
        for item in self.list_virtual_servers_raw():
            if not isinstance(item, dict) or not item:
                continue
            section_name = next(iter(item.keys()))
            section = item.get(section_name, {})
            if not isinstance(section, dict):
                continue
            rules.append({
                "name": section_name,
                "proto": section.get("proto", "all"),
                "src_dport_start": str(section.get("src_dport_start", "")),
                "src_dport_end": str(section.get("src_dport_end", "")),
                "dest_port": str(section.get("dest_port", "")),
                "dest_ip": section.get("dest_ip", ""),
            })
        return rules

    def get_virtual_servers(self) -> List[Dict[str, Any]]:
        return self.list_virtual_servers_raw()

    def add_virtual_server(
        self,
        src_port_start: int,
        src_port_end: Optional[int],
        dest_ip: str,
        dest_port: int,
        proto: str = "all",
    ) -> bool:
        rules = self.list_virtual_servers()
        indices = []
        for r in rules:
            name = r.get("name", "")
            if name.startswith("redirect_"):
                suffix = name.split("_", 1)[1]
                if suffix.isdigit():
                    indices.append(int(suffix))
        next_index = (max(indices) + 1) if indices else 1
        name = f"redirect_{next_index}"

        payload = {
            "firewall": {
                "table": "redirect",
                "name": name,
                "para": {
                    "proto": proto,
                    "src_dport_start": str(src_port_start),
                    "src_dport_end": str(src_port_end if src_port_end is not None else src_port_start),
                    "dest_ip": dest_ip,
                    "dest_port": str(dest_port),
                },
            }
        }
        return self._ds_request("add", payload) is not None

    def delete_virtual_server(self, name: str) -> bool:
        payload = {"firewall": {"name": [name]}}
        return self._ds_request("delete", payload) is not None
