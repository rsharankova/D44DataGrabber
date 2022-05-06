import sys,os
import re
import pkg_resources
required  = {'tkcalendar', 'pandas', 'matplotlib'} 
installed = {pkg.key for pkg in pkg_resources.working_set}
missing   = required - installed

try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import filedialog as fd
    from tkinter.messagebox import showerror
    from tkcalendar import Calendar, DateEntry
    from datetime import datetime, timedelta
    import data_grabber

    from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
    from matplotlib.backend_bases import key_press_handler
    from matplotlib.figure import Figure
    
except ImportError:
    sys.exit('''Missing dependencies. First run 
    pip install %s '''%(' '.join(missing)))


class MainFrame(ttk.Frame):
    def __init__(self, container):
        super().__init__(container)

        devlist_scroll=tk.Scrollbar(self)
        self.devlist=ttk.Treeview(self,yscrollcommand=devlist_scroll.set)
        devlist_scroll.config(command=self.devlist.yview)
        devlist_scroll.grid(column=3,row=0,rowspan=2,sticky=tk.N+tk.S)
        self.devlist['columns']=('device','node','event')
        self.devlist.column("#0",width=0,stretch=tk.NO)
        self.devlist.column("device",anchor=tk.CENTER,width=40)
        self.devlist.column("node",anchor=tk.CENTER,width=40)
        self.devlist.column("event",anchor=tk.CENTER,width=40)
        self.devlist.heading("#0",text="",anchor=tk.CENTER)
        self.devlist.heading("device",text="Device",anchor=tk.CENTER)
        self.devlist.heading("node",text="Node",anchor=tk.CENTER)
        self.devlist.heading("event",text="Event",anchor=tk.CENTER)
        self.devlist.grid(column=0,row=0,columnspan=3,rowspan=2,sticky = tk.NSEW)
    
        self.device=tk.Entry(self,width=16)
        self.device.insert(0,'Device')
        self.device.grid(column=0,row=2)
        self.device.bind("<FocusIn>",lambda x: self.device.selection_range(0, tk.END))
        self.node=tk.Entry(self,width=16)
        self.node.insert(0,'Node')
        self.node.grid(column=1,row=2)
        self.node.bind("<FocusIn>",lambda x: self.node.selection_range(0, tk.END))
        self.event=tk.Entry(self,width=16)
        self.event.insert(0,'Event')
        self.event.grid(column=2,row=2)
        self.event.bind("<FocusIn>",lambda x: self.event.selection_range(0, tk.END))

        self.buttoncell1 = tk.Frame(self)
        self.buttoncell1.grid(column=0, row=3, columnspan = 3, padx=10, pady=10, sticky=tk.W)
        
        ttk.Button(self.buttoncell1, text="Add to list", command=self.add_device).grid(column=0, row=0, padx=5, pady=5)
        ttk.Button(self.buttoncell1, text="Remove from list", command=self.remove_device).grid(column=1, row=0, padx=5, pady=5)
        ttk.Button(self.buttoncell1, text="Load parameter list", command=self.open_file).grid(column=3, row=0, padx=5, pady=5)

        self.enddate = datetime.now()
        self.startdate = self.enddate - timedelta(days=1)
        self.args_dict = {'debug':False, 'starttime':'', 'stoptime':'', 'outdir':'', 'paramlist':[]}
        #self.args_dict = container.args_dict
        self.df = None
        
        self.startcell=tk.Frame(self)
        self.startcell.grid(column=0,row=4,columnspan=3, padx=10, pady=10, sticky=tk.W)
        
        self.startdatelabel=tk.Label(self.startcell,text="Start:")
        self.startdatelabel.grid(column=0,row=0, sticky=tk.W)

        self.startdatecal = DateEntry(self.startcell,width=10,bg='white',fg='black',borderwidth=2)
        self.startdatecal.set_date(self.startdate)
        self.startdatecal.grid(column=1,row=0)        
        self.startdatecal.bind("<<DateEntrySelected>>", self.update_startdate)

        self.starth_spin = ttk.Spinbox(self.startcell, from_=0,to=23, width=4, wrap=True, command=self.update_starttime)
        self.starth_spin.grid(column=2,row=0)
        self.starth_spin.set(self.startdate.hour)
        self.startm_spin = ttk.Spinbox(self.startcell, from_=0,to=59, width=4, wrap=True, command=self.update_starttime)
        self.startm_spin.grid(column=3,row=0)
        self.startm_spin.set(self.startdate.minute)

        self.intvar = tk.StringVar()
        interval_opts = ['minutes=1','hours=1','days=1','weeks=1','months=1']
        self.interval = ttk.Combobox(self.startcell, textvar=self.intvar, values=interval_opts, width=8,justify='center')
        self.interval.option_add('*TCombobox*Listbox.Justify', 'center')
        self.interval.set('Interval')
        self.intvar.trace('w',self.set_start_interval)
        #self.interval.bind('<<ComboboxSelected>>',self.set_start_interval)        
        self.interval.grid(column=4, row=0)
        
        self.endcell=tk.Frame(self)
        self.endcell.grid(column=0,row=5, columnspan=3, sticky=tk.W, padx=10, pady=10)

        self.enddatelabel=tk.Label(self.endcell,text="  End:")
        self.enddatelabel.grid(column=0,row=0, sticky=tk.E)
         
        self.enddatecal = DateEntry(self.endcell,width=10,bg='white',fg='black',borderwidth=2)
        self.enddatecal.set_date(self.enddate)
        self.enddatecal.grid(column=1,row=0)
        self.enddatecal.bind("<<DateEntrySelected>>", self.update_enddate)

        self.endh_spin = ttk.Spinbox(self.endcell, from_=0,to=23, width=4, wrap=True, command=self.update_endtime)
        self.endh_spin.grid(column=2,row=0)
        self.endh_spin.set(self.enddate.hour)
        self.endm_spin = ttk.Spinbox(self.endcell, from_=0,to=59, width=4,wrap=True, command=self.update_endtime)
        self.endm_spin.grid(column=3,row=0)
        self.endm_spin.set(self.enddate.minute)

        ttk.Button(self.endcell, text="Now", command=self.set_end_now).grid(column=4, row=0)

        self.buttoncell2 = tk.Frame(self)
        self.buttoncell2.grid(column=0, row=6, columnspan = 3, padx=10, pady=10, sticky=tk.W)

        ttk.Button(self.buttoncell2, text="Get data", command=self.get_data).grid(column=0, row=0, padx=5, pady=5)
        ttk.Button(self.buttoncell2, text="Plot data", command=self.plot_data).grid(column=1, row=0, padx=5, pady=5)
        ttk.Button(self.buttoncell2, text="Save to file", command=self.save_to_file).grid(column=2, row=0, padx=5, pady=5)
        ttk.Button(self.buttoncell2, text="Quit", command=container.destroy).grid(column=3, row=0)

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot()
        self.ax.set_xlabel("time [s]")
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)  # A tk.DrawingArea.
        self.canvas.draw()
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.grid(column=0, row=7, columnspan=3)
        self.canvas.get_tk_widget().grid(column=0, row=8, columnspan=3)
        
        self.grid(padx=10, pady=10, sticky=tk.NSEW)
        
    def add_device(self):
        if "Device" in self.device.get():
            return
        self.devlist.insert(parent='',index='end',iid=len(self.devlist.get_children()),text='',
                       values=(self.device.get(),self.node.get(),self.event.get()))
        print(self.devlist.get_children())
        
    def remove_device(self):
        selected_devs = self.devlist.selection()        
        for dev in selected_devs:          
            self.devlist.delete(dev)

    def open_file(self):
        filename = fd.askopenfilename()
        try:
            f=open(filename,'r')
            for l in f:
                self.devlist.insert(parent='',index='end',iid=len(self.devlist.get_children()),text='',
                                    values=(l.split()))
        except ValueError as error:
            showerror(title='Error',message=error)
            
    def get_data(self):
        print("Start",self.startdate.isoformat(timespec='seconds'))
        print("End",self.enddate.isoformat(timespec='seconds'))

        if self.startdate >= self.enddate:
            print('Select Start time earlier than End time')
            return
        
        self.args_dict['starttime'] = '{0:%Y-%m-%d+%H:%M:%S}'.format(self.startdate)
        self.args_dict['stoptime'] = '{0:%Y-%m-%d+%H:%M:%S}'.format(self.enddate)
        self.args_dict['paramlist']=[]
        for line in self.devlist.get_children():
            self.args_dict['paramlist'].append(self.devlist.item(line)['values'])
            
        self.args_dict['debug'] = True
    
        # fetch data
        self.df = data_grabber.fetch_data(self.args_dict)
        
    def plot_data(self):
        ts = [key for key in list(self.df.keys()) if key.find('tstamp')!=-1]
        data = [key for key in list(self.df.keys()) if key.find('tstamp')==-1]
        print(ts, data)
        for t,d in zip(ts,data):
            self.ax.plot(self.df[t],self.df[d])
        self.canvas.draw()


    def save_to_file(self):
        filename = fd.asksaveasfilename(initialdir=os.getcwd(),filetypes=[('Comma-separated text','*.csv')])
        try:
            data_grabber.save_to_file(self.args_dict,self.df,filename)
        except ValueError as error:
            showerror(title='Error',message=error)

    def update_startdate(self,event):
        self.startdate = self.startdate.replace(year=self.startdatecal.get_date().year, month=self.startdatecal.get_date().month, day=self.startdatecal.get_date().day)

    def update_enddate(self,event):
        self.enddate = self.enddate.replace(year=self.enddatecal.get_date().year, month=self.enddatecal.get_date().month, day=self.enddatecal.get_date().day)

    def update_starttime(self):
        self.startdate = self.startdate.replace(hour=int(self.starth_spin.get()),minute=int(self.startm_spin.get()))

    def update_endtime(self):
        self.enddate = self.enddate.replace(hour=int(self.endh_spin.get()),minute=int(self.endm_spin.get()))

    def set_end_now(self):
        self.enddate = datetime.now()
        self.enddatecal.set_date(self.enddate)
        self.endh_spin.set(self.enddate.hour)
        self.endm_spin.set(self.enddate.minute)

    def set_start_interval(self,*args):
        match=re.findall(r'(seconds|minutes|hours|days|weeks|months)=(\d+)',self.interval.get())
        if match:
            self.startdate=self.enddate-timedelta(**{x:int(y) for (x,y) in match})
            
        self.startdatecal.set_date(self.startdate)
        self.starth_spin.set(self.startdate.hour)
        self.startm_spin.set(self.startdate.minute)
                
class DataGrabber(tk.Tk):
        def __init__(self):
                super().__init__()

                self.title('D44 Data Grabber')
                self.geometry('500x500')
                self.resizable(True,True)

                self.args_dict = {'debug':False, 'starttime':'', 'stoptime':'', 'outdir':'', 'paramlist':[]}
                self.df = None

if __name__ =="__main__":
        app = DataGrabber()
        MainFrame(app)
        app.mainloop()

