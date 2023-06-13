import smbus
import time

MAX_BYTES = 2039

bus = smbus.SMBus(1)
 
 # (PAR, N bytes):
_pars = [('DOB', 16),    # date of birth
         ('UID', 16),    # exp date time 4bytes extra
         ('SEX', 16),    # M/F or others
         ('GEN', 16),    # genetic background
         ('ZYG', 4),     # Hom/het zygote
         ('SPC', 16),    # species
         ('LOC', 16),    # location
         ('VER', 16),    # Version
         ('UPD', 16),    # Last updated (date)
         ("ST", 4, 8),    # Settings. last number indicates settings to create
         ('OTH', None),] # other

template = {}

loc = 0
for par in _pars:
    if par[0] == "ST":
        # settings:
        for i in range(par[2]):
            if i >= MAX_BYTES:
                continue

            template.update({"ST{}".format(i): 
                                {"addr": (loc, loc + par[1])}})
            loc += par[1]
    
    else:        
        if par[0] == "OTH":
            template.update({par[0]: {"addr": (loc, MAX_BYTES)}})
        else:
            template.update({par[0]: {"addr": (loc, loc + par[1])}})
            loc += par[1]



class MemChip():
    addr_prefix = 0b1010  # prefix for address
    ref = template
    stop_chr = chr(182) # 182 = ¶

    def convert_2_addr(self, loc):
        if loc > MAX_BYTES:
            return
        loc, reg = loc // 0xFF, loc % 0xFF
        return (self.addr_prefix << 3 | loc), reg
  
    def read(self, par):
        # reads from chip returns string
        out = ""
        for i in range(*self.ref[par]["addr"]):
            out = out + chr(bus.read_byte_data(*self.convert_2_addr(i)))
            if out[-1] == self.stop_chr:
                return out[:-1]
        return out
    
    def write(self, par, data):
        if not isinstance(data, str):
            data = str(data)

        # Don't write stop chr:
        data = "".join([i for i in data if i != self.stop_chr])

        # add stop chr at the end
        data = [i for i in data + self.stop_chr]

        for i, pos in enumerate(range(*self.ref[par]["addr"])):
            if i >= len(data):
                return

            else:
                bus.write_byte_data(*self.convert_2_addr(pos), 
                                    ord(data[i]))
            time.sleep(0.005)


if __name__ == "__main__":
    m = MemChip()