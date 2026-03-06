import urllib.parse
from typing import Optional, Dict, Any, List

from chattool.utils.httpclient import HTTPClient
from chattool.config import TPLinkConfig

class TPLogin(HTTPClient):
    def __init__(self, url: str = None, password: str = None):
        self.url = url or TPLinkConfig.TPLOGIN_URL.value
        self.password = password or TPLinkConfig.TPLOGIN_AUTH_PASSWORD.value
        
        if not self.url:
            raise ValueError("TPLOGIN_URL not set")
        
        super().__init__(api_base=self.url)
        self.stok = None

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
        key = "RDpbLfCPsJZ7fiv"
        dictionary = "yLwVl0zKqws7LgKPRQ84Mdt708T1qQ3Ha7xv3H7NyU84p21BriUWBU43odz3iP4rBL3cD02KZciXTysVXiV8ngg6vL48rPJyAUw0HurW20xqxv9aYb4M9wK1Ae0wlro510qXeU07kV57fQMc8L6aLgMLwygtc0F10a0Dg70TOoouyFhdysuRMO51yY5ZlOZZLEal1h0t9YQW0Ko7oBwmCAHoic4HYbUyVeU3sfQ1xtXcPcf1aT303wAQhv66qzW"
        return self._security_encode(key, password, dictionary)

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
            response = self.post("/", data=payload)
            data = response.json()
            
            if data.get("error_code") == 0:
                stok = data.get("stok")
                self.stok = urllib.parse.unquote(stok)
                self.logger.info(f"Login successful")
                return self.stok
            else:
                self.logger.error(f"Login failed: {data}")
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

        url = f"/stok={urllib.parse.quote(stok)}/ds"
        body = {"method": method}
        body.update(payload)

        try:
            response = self.post(url, data=body)
            data = response.json()
            if data.get("error_code") == 0:
                return data
            else:
                self.logger.error(f"API request failed: {data}")
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
