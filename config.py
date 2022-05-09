import json

class config():
    def __init__(self):
        self.properties=["active","node","event","line_style","line_color","marker_style","marker_color"]
        self.cfgdict={}
        
    def load_config(self,config_file):
        try:
            with open(config_file,'r') as cfg:
                self.cfgdict=json.load(cfg)
        except IOError:
            self.cfgdict={}

    def save_config(self,config_file):
        with open(config_file, "w") as fout:
            json.dump(self.cfgdict, fout)

    def get_style(self,device, what):
        return self.cfgdict[device][what] if device in self.cfgdict and what in self.cfgdict[device] else None
    
    def get_list_of_devices(self,all=False):
        devs=[]
        for k,d in self.cfgdict.items():
            if d["active"]==True or all:
                devs.append((k,d["node"],d["event"]))
        return devs

    def update_device(self,**args):
        if args["device"] in self.cfgdict:
            for k,i in args.items():
                if k in self.properties:
                    self.cfgdict[args['device']][k]=i
        
        else:
            self.cfgdict[args["device"]]={}
            for k in self.properties:
                if k in args:
                    self.cfgdict[args["device"]][k]=args[k]
                else:
                    self.cfgdict[args["device"]][k]=None

    def print_config(self):
        for k,i in self.cfgdict.items():
            print(k,i)
