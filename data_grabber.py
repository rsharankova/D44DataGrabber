import os, re
from datetime import datetime, timedelta
from urllib.request import urlopen
import argparse
import pandas as pd

def parse_args(args_dict):
    ### Make a parser
    parser = argparse.ArgumentParser(description="usage: %prog [options] <input file.ROOT> \n")
    ### Add options
    parser.add_argument ('-v', dest='debug', action="store_true", default=False,
                         help="Turn on verbose debugging. (default: False)")
    parser.add_argument ('--stopat',  dest='stopat', default='',
                         help="YYYY-MM-DD+hh:mm:ss (default: now)")
    parser.add_argument ('--days', dest='days', type=float, default=0,
                         help="Days before start time to request data? (default: %(default)s).")
    parser.add_argument ('--hours', dest='hours', type=float, default=0,
                         help="Hours before start time to request data? (default: %(default)s)")
    parser.add_argument ('--minutes', dest='minutes', type=float, default=0,
                         help="Minutes before start time to request data? (default: %(default)s)")
    parser.add_argument ('--seconds', dest='seconds', type=float, default=0,
                         help="Seconds before start time to request data? (default: %(default)s unless all are zero, then 1).")
    parser.add_argument ('--outdir',  dest='outdir', default='',
                         help="Directory to write final output file. (default: pwd)")
    parser.add_argument ('--paramfile',  dest='paramlistfile', default='ParamList.txt',
                         help="Parameter list file name. (default: ParamList.txt)")

    ### Get the options and argument values from the parser
    options = parser.parse_args()
    debug     = options.debug
    stoptime  = options.stopat
    days      = options.days    
    hours     = options.hours   
    minutes   = options.minutes 
    seconds   = options.seconds 
    outdir    = options.outdir
    paramlistfile = options.paramlistfile


    # Datetime for when to stop the reading
    today = datetime.today()

    if stoptime == '': #Default: Now
        stoptime = '{0:%Y-%m-%d+%H:%M:%S}'.format(today )

    
    # If no time interval set, default to 1 second
    if days == 0 and hours == 0 and minutes == 0 and seconds == 0: seconds = 1


    # Build a datetime interval to offset starttime before stoptime. 
    interval = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    # Set the time to start the data-series request window
    starttime = '{0:%Y-%m-%d+%H:%M:%S}'.format(datetime.strptime(stoptime,'%Y-%m-%d+%H:%M:%S') - interval)
    
    
    if debug:
        print ('Data request start time:' + starttime)
        print ('Data request stop time:' + stoptime)

    if outdir == '': outdir = os.getcwd()

    args_dict['debug'] = debug
    args_dict['starttime'] = starttime
    args_dict['stoptime'] = stoptime
    args_dict['outdir'] = outdir
    args_dict['paramlist'] = load_paramlist(textfilename = paramlistfile, debug=args_dict['debug'])


def load_paramlist(textfilename='ParamList.txt', debug=False):
    
    if debug: print ('Opening %s'%textfilename)

    if not os.path.isfile(textfilename):
        exit ('File %s is not a file.'%textfilename)

    textfile = open(textfilename,'r')
    lines = textfile.readlines()
    devlist = []

    for line in lines:
        cols = line.strip().split(' ')
        if not len(cols) == 3:
            print (line + " > 3 items in line.")
            continue

        devlist.append(cols) #device, node, event
        
    if debug: print (devlist)
    return devlist


def find_nodes(deviceName):

    nodelist = []
    tempURL= "https://www-ad.fnal.gov/cgi-bin/acl.pl?acl=show/whereLogged+%s"%deviceName
    # Download node data to a string                                                                                                                      
    response = urlopen(tempURL)
    lines = response.read().decode('utf-8').split('\n')
    for line in lines:
        if line.find('%s'%deviceName) !=-1:
            cols = line.split() # Name, Node, List (2 cols), Data Event
            if re.match(r'.*(Sec|Min|Hz|Event).*',cols[2]+cols[3]):
                nodelist.append((cols[1],cols[-1]))                   

    return nodelist

def fetch_data(args_dict):
    # logger_get ACL command documentation: https://www-bd.fnal.gov/issues/wiki/ACLCommandLogger_get
    URL = "http://www-ad.fnal.gov/cgi-bin/acl.pl?acl=logger_get/date_format='utc_seconds'/ignore_db_format/start=\""+args_dict['starttime']+"\"/end=\""+args_dict['stoptime']+"\""

    df = pd.DataFrame()
    status = [None]*len(args_dict['paramlist'])
    for j,(deviceName, node, evt) in enumerate(args_dict['paramlist']):

        tempURL = URL
        # Node
        if node !='Node':
            tempURL = tempURL+"/node="  + node
        # Event
        if evt !='Event':
            tempURL = tempURL+"/data_event=" + evt
        # URL for getting this device's data
        tempURL = tempURL + '+' + deviceName
        if args_dict['debug']: print (tempURL)

        # Download device data to a string
        response = urlopen(tempURL)
        if response is None:
            if args_dict['debug']: print (tempURL+"\n got no reponse.")
            continue

        str1 = response.read().decode('utf-8').split('\n')
        if str1[0].find('No values') !=-1: 
            if args_dict['debug']: print (tempURL+"\n "+str1[0])
            status[j] = str1[0]
            continue

        ts1 = []
        data1 = []
        for line in str1:
            if len(line)<=0:
                continue

            cols = line.split()
            ts1.append(cols[0])
            data1.append(cols[1])


        dfloc=pd.DataFrame({'tstamp_%s'%deviceName: [float(e) for e in ts1],
                            deviceName: [float(d) for d in data1]})
        if df.empty:
            df=dfloc
            
        else:
            df=df.merge(dfloc,how="outer",left_index=True,right_index=True)


    if args_dict['debug']:
        print(df)
        
    return status,df

def save_to_file(args_dict, df, nameoverride=''):
    if nameoverride !='':
        df.to_csv(nameoverride,header=True,index=False)
    else:
        outfilename   =   os.path.join(args_dict['outdir'],r'DataLogger_From_%s_to_%s.csv'%(args_dict['starttime'],args_dict['stoptime']))
        df.to_csv(outfilename,header=True,index=False)

        
def main():

    args_dict = {'debug':False, 'starttime':'', 'stoptime':'', 'outdir':'', 'paramlist':[]}
    parse_args(args_dict)

    status,df = fetch_data(args_dict)
    save_to_file(args_dict,df,'./DataLogger.csv')

if __name__ == "__main__":
    main()
