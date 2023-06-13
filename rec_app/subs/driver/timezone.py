"""
wrapper for timedatectl to set timezone on rpi

"""
from os import popen


class TimeZone():
    timezones = {}
    current = {}

    region = ""
    continent = ""

    def __init__(self) -> None:
        self.timezones = self.get_tz_list()
        self.current = self.get_status()
        self.parse_current_region_continent()

    def set_timezone(self, continent, region) -> tuple:
        if (not continent in self.timezones 
            or not region in self.timezones[continent]):
            return
        
        if region:
            region = "/" + region
        self.tdctl(f"set-timezone {continent}{region}", prefix="sudo")
        self.current = self.get_status()
        return self.parse_current_region_continent()


    def get_tz_list(self,) -> dict:
        """
        reads all timezones and creates a dict with timezones

        """

        out = self.tdctl("list-timezones")
        if not any(out):
            return {}
        
        return self.parse_tzs(out)

    def get_status(self) -> dict:
        out = self.tdctl("status")
        return self.parse_status(out)
    
    def parse_current_region_continent(self):
        _current = self.current.get("Time zone")
        if _current is None:
            return
        _current = _current.split(" ")[0].split("/")
        if len(_current) > 1:
            self.continent, self.region = _current[0], _current[1]
        else:
            self.continent, self.region = _current, ""
        return self.continent, self.region

    @staticmethod
    def tdctl(cmd, prefix=""):
        """
        launch timedatectl with cmd
        """
        return popen(f"{prefix} timedatectl {cmd}").read().split("\n")

    @staticmethod
    def parse_status(res) -> dict:
        out = {}
        for i in res:
            if i:
                split = i.index(":")
                key  = i[0:split].lstrip(" ")
                out[key] = i[split + 1:].rstrip(" ").lstrip(" ")
        return out

    @staticmethod
    def parse_tzs(res) -> dict:
        """
        parses list with timezones to dict

        """
        out = {}
        for i in res:
            if not i:
                continue
            
            i = i.split("/")
            
            if len(i) == 1:
                i.append("")
            
            if i[0] not in out:
                out[i[0]] = set()
            
            out[i[0]].add(i[1])

        return out


# TODO: use re to parse