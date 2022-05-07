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
    from tkinter.messagebox import showerror, showwarning
    from tkcalendar import Calendar, DateEntry
    from datetime import datetime, timedelta
    import data_grabber

    from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
    from matplotlib.backend_bases import key_press_handler
    from matplotlib.figure import Figure
    import matplotlib.colors as mcolors
    from matplotlib import pyplot as plt
    
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
        plotWin = PlotDialog(self)

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

class PlotDialog(tk.Toplevel, object):
    def __init__(self,parent):
        super().__init__(parent)
        self.title("Data")

        plt.rcParams["axes.titlelocation"] = 'right'
        overlap = {name for name in mcolors.CSS4_COLORS
                   if f'xkcd:{name}' in mcolors.XKCD_COLORS}

        overlap.difference_update(['aqua','white','ivory','lime','chocolate','gold'])
        self.colors = [mcolors.XKCD_COLORS[f'xkcd:{color_name}'].upper() for color_name in sorted(overlap)]
        self.colornames = sorted(overlap)
        
        ts = [key for key in list(parent.df.keys()) if key.find('tstamp')!=-1]
        data = [key for key in list(parent.df.keys()) if key.find('tstamp')==-1]
        
        self.fig = Figure(figsize=(10,5))
        self.ax = [None]*len(data)
        self.ax[0] = self.fig.add_subplot(111)
        for i in range(1,len(data)):
            self.ax[i] = self.ax[0].twinx()
        self.ax[0].set_xlabel("time")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()        
        #self.toolbar = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
        self.toolbar = MyToolbar(self.canvas,self)
        self.toolbar.update()
        self.canvas.get_tk_widget().grid(column=0, row=0, sticky=tk.NSEW )
        self.toolbar.grid(column=0, row=1, columnspan=3, sticky = tk.W + tk.E)
        
        for i,(t,d) in enumerate(zip(ts,data)):
            space= space + '  '*(len(d)+1) if i>0 else ''
            self.ax[i].set_title(d+space,color=self.colors[i],ha='right',fontsize='large')                                
            self.ax[i].tick_params(axis='y', colors=self.colors[i], labelsize='large',rotation=90)
            tstamps=parent.df[t].apply(lambda x: datetime.fromtimestamp(x) if x==x else x)
            self.ax[i].plot(tstamps,parent.df[d],c=self.colors[i],label=d)

            if i%2==0:
                self.ax[i].yaxis.tick_left()
                for yl in self.ax[i].get_yticklabels():
                    yl.set_x( -0.025*(i/2.) )
                    yl.set(verticalalignment='bottom')
                    
            else:
                self.ax[i].yaxis.tick_right()
                for yl in self.ax[i].get_yticklabels():
                    yl.set_x( 1.0+0.025*(i-1)/2.)
                    yl.set(verticalalignment='bottom')
                                        
        self.fig.subplots_adjust(left=0.12)
        self.fig.subplots_adjust(right=0.88)
        self.fig.subplots_adjust(bottom=0.12)
        self.fig.subplots_adjust(top=0.88)

        self.canvas.draw()
        
class MyToolbar(NavigationToolbar2Tk):
  def __init__(self, figure_canvas, window):
      self.toolitems = [*NavigationToolbar2Tk.toolitems]
      self.toolitems.insert(
          [name for name, *_ in self.toolitems].index("Subplots") + 1,
          ("Customize", "Edit axis, curve and image parameters",'qt4_editor_options','edit_parameters'))

      NavigationToolbar2Tk.__init__(self, figure_canvas,window, pack_toolbar=False)

  def edit_parameters(self):
    self.edit = EditDialog(self)
        

  def apply_style(self):
      axes = self.window.ax
      item = self.edit.axselect.get()
      if axes and len(self.edit.titles)>0 and item!='':
          ax = axes[self.edit.titles.index(item)]
          if self.edit.colselect.get() !='':
              ax.get_lines()[0].set_color(self.edit.colselect.get())
              ax.tick_params(colors=self.edit.colselect.get(), which='both',axis='y')
              ax.set_title(ax.get_title('right'),color=self.edit.colselect.get(),ha='right',fontsize='large')
          ymin = self.edit.yminselect.get()
          ymax = self.edit.ymaxselect.get()
          if ymin != '' and ymax !='' and float(ymax)>float(ymin):
              ax.set_ylim(float(ymin),float(ymax))
          self.canvas.draw()

class EditDialog(tk.Toplevel, object):
    def __init__(self,parent):
        super().__init__(parent)
        self.title("Edit properties")
        #self.geometry("200x200")

        axes = parent.window.ax
        self.titles = []
        if not axes:
            showwarning('Warning','There are no axes to edit')
            
        else:
            self.titles = [
                ax.get_label().strip() or
                ax.get_title().strip() or
                ax.get_title('left').strip() or
                ax.get_title('right').strip() or
                " - ".join(filter(None, [ax.get_xlabel(), ax.get_ylabel()])) or
                f"<anonymous {type(ax).__name__}>"
                for ax in axes]

        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.editframe = tk.Frame(self)
        self.editframe.grid(column=0,row=0, sticky=tk.NSEW, padx=10, pady=10)

        self.axlabel = tk.Label(self.editframe,text='Select axis:')
        self.axlabel.grid(column=0, row=0)
        self.axselect = ttk.Combobox(self.editframe, values=self.titles, width=10,justify='left')
        self.axselect.option_add('*TCombobox*Listbox.Justify', 'center')
        self.axselect.grid(column=1,row=0)
        self.collabel = tk.Label(self.editframe, text='Color:')
        self.collabel.grid(column=0,row=1)
        self.colselect = ttk.Combobox(self.editframe, values = parent.window.colornames, width=10, justify='left' )
        self.colselect.option_add('*TCombobox*Listbox.Justify', 'center')
        self.colselect.grid(column=1,row=1)
        self.yminlabel = tk.Label(self.editframe, text='Y min:')
        self.yminlabel.grid(column=0,row=2)
        self.yminselect=tk.Entry(self.editframe,width=10)
        self.yminselect.insert(0,'0.0')
        self.yminselect.bind("<FocusIn>",lambda x: self.yminselect.selection_range(0, tk.END))    
        self.yminselect.grid(column=1,row=2)
        self.ymaxlabel = tk.Label(self.editframe, text='Y max:')
        self.ymaxlabel.grid(column=0,row=3)
        self.ymaxselect=tk.Entry(self.editframe,width=10)
        self.ymaxselect.insert(0,'0.0')
        self.ymaxselect.bind("<FocusIn>",lambda x: self.ymaxselect.selection_range(0, tk.END))    
        self.ymaxselect.grid(column=1,row=3)

        ttk.Button(self.editframe, text="Apply style", command=parent.apply_style).grid(column=0, row=4)
        ttk.Button(self.editframe, text="Close", command=self.destroy).grid(column=1, row=4)

    
class DataGrabber(tk.Tk):
        def __init__(self):
                super().__init__()

                self.title('D44 Lite')
                self.geometry('500x500')
                self.resizable(True,True)

                self.args_dict = {'debug':False, 'starttime':'', 'stoptime':'', 'outdir':'', 'paramlist':[]}
                self.df = None

if __name__ =="__main__":
        app = DataGrabber()
        MainFrame(app)
        app.mainloop()

