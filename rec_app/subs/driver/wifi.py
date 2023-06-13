"""
simple python wrapper for wpa_cli 
to connect to wifi from linux cli


"""
from os import popen


INTERFACE = "-i wlan0"


class RpiWifi():
    """
    Wifi controller for RPI and other linux based systems
    wraps wpa_cli
    """

    ip = ""
    status = {}
    scan_results = {}
    known_nws = {}

    def __init__(self) -> None:
        self.get_ip()
        self.known_networks()
        pass

    # main functions use these
    def connect(self, ssid, passwd=None) -> None:
        if ssid in self.known_nws:
            if not passwd:
                self.connect_exist_ssid(ssid)
            else:
                self.edit_passwd(ssid, passwd)
        else:
            self.connect_new_ssid(ssid, passwd)
        self.known_networks()
        self.check_connection()
    
    def connect_new_ssid(self, ssid, passwd) -> None:
        """
        connect to a new network using ssid & password
        """
        net_no = self.new_network()
        res = self.ssid_pass(ssid, passwd, net_no)
        if res:
            self.connect_network(net_no)

    def edit_passwd(self, ssid, passwd) -> None:
        """
        edit password of know network,
        based on ssid
        """
        net_no = self._get_net_no_from_ssid(ssid)
        self.ssid_pass(ssid, passwd, net_no)
        self.connect_network(net_no)

    def connect_exist_ssid(self, ssid) -> None:
        """
        connect to existing network
        """
        net_no = self._get_net_no_from_ssid(ssid)
        self.connect_network(net_no)

    def check_connection(self, *args) -> bool:
        res = self.get_status()
        self.parse_status(res)
        return True if self.status.get("wpa_state") == "COMPLETED" else False

    def remove_known_ssid(self, ssid) -> None:
        net_no = self._get_net_no_from_ssid(ssid)
        self.remove_network(net_no)

    def get_ip(self) -> str:
        _ip = self.parse_status(self.get_status())
        ip = _ip.get("ip_address")
        if ip:
            self.ip = ip
            return ip
    
    def scan(self, sort=True, sort_on="signal level", reverse=False):
        """
        scan for wifi and sort on subkey if sort is on
        returns dict with the results
        """

        self.trigger_scan_wpa()
        # TODO: wait in thread here or kv clock
        res = self.scan_wpa_results()
        if not any(res):
            return
        res = self.parse_res(res)
        if sort:
            res = self.sort_res(res, subkey=sort_on, reverse=reverse)
        return res
    
    def known_networks(self):
        res = self.get_known_networks()
        return self.parse_res(res, output="known_nws")

    # helper functions, avoid using these directly
    def ssid_pass(self, ssid, passwd, net_no=0, *args) -> bool:
        """
        sets ssid and passwd
        """
        if not 8 <= len(passwd) < 64:
            print("password should be between 8 and 63 characters")
            return False
            
        # set ssid
        res = self.wpa(f'set_network {net_no} ssid \'\"{ssid}\"\'')
        if not "OK" in res:
            print("Error setting ssid:", res)
        
        # set passwd
        res = self.wpa(f'set_network {net_no} psk \'\"{passwd}\"\'')
        if not "OK" in res:
            print("Error setting psk:", res)
        
        self.reconnect()
        return True
        
    def new_network(self) -> int:
        res = self.wpa("add_network")
        return int(res[0]) # res is network no

    def remove_network(self, net_no) -> list:
        res = self.wpa(f"remove_network {net_no}")
        return res # res is network no

    def get_known_networks(self, *args) -> list:
        """
        returns list of known networks
        """
        res = self.wpa("list_networks")
        return res

    def connect_network(self, net_no) -> list:
        res = self.wpa(f"select_network {net_no}")
        return res

    def get_status(self) -> list:
        """
        returns network status
        """
        res = self.wpa("status")
        return res

    def reconnect(self) -> list:
        return self.wpa("reassociate")   # needed to connect to existing network which was already selected

    def trigger_scan_wpa(self) -> list:
        """
        start scan
        use scan_wpa_results to see result
        outputs OK if working
        """
        res = self.wpa("scan")
        return res

    def scan_wpa_results(self) -> bool:
        res = self.wpa("scan_results")
        return res

    def scan_iwlist(self, *args) -> list:
            """
            alternative for using wpa
            scans wifi on rpi and returns list with available ssids
            """
            list_out = []
            for l in popen("sudo iwlist wlan0 scan | grep 'ESSID'").read().split("\n"):   # must be sudo
                l = l.lstrip(" ")
                if l.startswith("ESSID:"):
                    list_out.append(l[len("ESSID:")+1:-1])
            return list_out

    def _get_net_no_from_ssid(self, ssid) -> int:
        net_list = self.get_known_networks()
        net_list = self.parse_res(net_list, output="known_nws")  # create dict of ssids and net_nos
        return int(net_list[ssid]["network id"])

    @staticmethod
    def wpa(cmd):
        """
        wrapper for wpa_cli
        returns output as list (each line is an item)
        """
        return popen(f"wpa_cli {INTERFACE} {cmd}").read().split("\n")
  
    def parse_status(self, status) -> dict:
        """
        parses status to dict
        """
        self.status = {}
        for i in status:
            try:
                self.status.update([i.split("=")])
            except ValueError:
                pass
        return self.status
    
    def parse_res(self, scan_res, key='ssid', output="scan_results") -> dict:
        """
        take wpa scan results and parse to dict.
        WORKS ALSO FOR KNOWN NETWORKS
        key indicates the main dict keys (defaults to ssid name)
        each item has a subdict with all the found pars
        """
        out = {}
        idx_list, scan_res = scan_res[0], scan_res[1:]
        idx_list = idx_list.split(" / ")

        for res in scan_res:
            if not res:
                continue
            res = res.split("\t")
            _out = dict([(idx, i) for idx, i in zip(idx_list, res)])
            out[_out[key]] = _out
        setattr(self, output, out)      # save output
        return out

    @staticmethod
    def sort_res(res, subkey="signal level", reverse=False):
        """
        sorts scanning results or other dict based on sub key
        for example to sort scan results on signal strength:
        use sort_res(scan_results, subkey="signal level")
        use reverse to reverse results
        """
        return  {k: v for k, v in 
                 sorted(res.items(), 
                        key=lambda d: d[1][subkey], 
                        reverse=reverse)}


# for testing
if __name__ == "__main__":
    wifi = RpiWifi()
    print(wifi.status)

# TODO: use re to parse