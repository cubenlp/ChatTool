import json
import urllib.parse
from typing import Optional, Dict, Any, List

from chattool.utils.httpclient import HTTPClient
from chattool.config import TPLinkConfig

class TPLogin(HTTPClient):
    """
    TP-Link Router Client
    
    Reverse engineered from TL-WDR5620 web interface.
    """
    def __init__(self, url: str = None, password: str = None):
        self.url = url or TPLinkConfig.TPLOGIN_URL.value
        self.password = password or TPLinkConfig.TPLOGIN_AUTH_PASSWORD.value
        
        if not self.url:
            raise ValueError("TPLOGIN_URL not set")
        
        super().__init__(api_base=self.url)
        self.stok = None

    def _security_encode(self, key, password, dictionary):
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

    def _org_auth_pwd(self, password):
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
            # Note: headers are handled by HTTPClient, but we might need explicit content type if default isn't enough
            # httpx sets application/json automatically when json=... is used
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

    def get_stok(self):
        if not self.stok:
            self.login()
        return self.stok

    def _api_request(self, method: str, module: str, action: str, params: Dict = None) -> Optional[Dict]:
        stok = self.get_stok()
        if not stok:
            return None
            
        url = f"/stok={urllib.parse.quote(stok)}/ds"
        
        payload = {
            "method": method,
            module: params or {"name": "info"} # Default params often needed
        }
        
        # If action is specified, it might be part of the module dict or separate?
        # Based on reverse engineering:
        # {"method": "get", "device_info": {"name": "info"}}
        # {"method": "get", "firewall": {"table": "redirect"}}
        
        # So we can just pass the payload structure directly via params if it's complex, 
        # or construct it here.
        # Let's make it flexible.
        
        try:
            response = self.post(url, data=payload)
            data = response.json()
            if data.get("error_code") == 0:
                return data
            else:
                self.logger.error(f"API request failed: {data}")
                return None
        except Exception as e:
            self.logger.error(f"Error during API request: {e}")
            return None

    def get_device_info(self):
        return self._api_request("get", "device_info", "info", {"name": "info"})

    def get_virtual_servers(self):
        # {"method": "get", "firewall": {"table": "redirect"}}
        data = self._api_request("get", "firewall", "table", {"table": "redirect"})
        if data:
            return data.get("firewall", {}).get("redirect", [])
        return []
