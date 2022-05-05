import os
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
                         help="YYYY-MM-DD hh:mm:ss (default: now)")
    parser.add_argument ('--maxcount',  dest='maxcount', default=-1,
                         help="Number of devices in list to process. (default: -1 = all)")
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
    stopat    = options.stopat
    maxcount  = int(options.maxcount)
    days      = options.days    
    hours     = options.hours   
    minutes   = options.minutes 
    seconds   = options.seconds 
    outdir    = options.outdir
    paramlistfile = options.paramlistfile


    # Datetime for when to stop the reading
    today = datetime.today()

    stoptime = ''
    if stopat == '': #Default: Now
        stoptime = '{0:%Y-%m-%d+%H:%M:%S}'.format(today )
    else:            # or attempt to use the string passed in by user
        stopdt = datetime.strptime(stopat,'%Y-%m-%d %H:%M:%S')
        stoptime = '{0:%Y-%m-%d+%H:%M:%S}'.format(stopdt)

    if debug: print ("Stop time: "+stoptime)
    
    # If no time interval set, default to 1 second
    if days == 0 and hours == 0 and minutes == 0 and seconds == 0: seconds = 1

    if debug:
        print ("Time interval: days = "+str(days)+
               ", hours = "  +str(hours  )+
               ", minutes = "+str(minutes)+
               ", seconds = "+str(seconds)+".")


    # Build a datetime interval to offset starttime before stoptime. 
    interval = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    # Set the time to start the data-series request window
    starttime = '{0:%Y-%m-%d+%H:%M:%S}'.format(stopdt - interval)
    
    
    if debug:
        print ('Data request start time:' + starttime)
        print ('Data request stop time:' + stoptime)

    if outdir == '': outdir = os.getcwd()

    args_dict['debug'] = debug
    args_dict['maxcount'] = maxcount
    args_dict['starttime'] = starttime
    args_dict['stoptime'] = stoptime
    args_dict['outdir'] = outdir
    args_dict['paramlist'] = getParamListFromTextFile(textfilename = paramlistfile, debug=args_dict['debug'])


def getParamListFromTextFile(textfilename='ParamList.txt', debug=False):
    
    if debug: print ('getParamListFromTextFile: Opening %s'%textfilename)
    # Bail if no file by that name                                                                                                                                                  
    if not os.path.isfile(textfilename): exit ('File %s is not a file.'%textfilename)
    textfile = open(textfilename,'r')
    lines = textfile.readlines()
    finallist = []
    for line in lines:
        cleanline = line.strip()
        parts = cleanline.split(' ')
        if not len(parts) == 3:
            print (line+"  ...unable to parse node, device and event.")
            continue
        node,device,evt = parts[0],parts[1],parts[2]
        finallist.append([node,device,evt])
    if debug: print (finallist)
    return finallist


def fetch_data(args_dict):
    # logger_get ACL command documentation: https://www-bd.fnal.gov/issues/wiki/ACLCommandLogger_get
    URL = "http://www-ad.fnal.gov/cgi-bin/acl.pl?acl=logger_get/date_format='utc_seconds'/ignore_db_format/start=\""+args_dict['starttime']+"\"/end=\""+args_dict['stoptime']+"\""

    # Loop over device names, retrieving data from the specified logger node
    maxcount = len(args_dict['paramlist']) if args_dict['maxcount'] < 0 else args_dict['maxcount']
    devicecount = 0
    df = pd.DataFrame()
    for node, deviceName, evt in args_dict['paramlist']:
        # Allows early stopping for development dolphins
        devicecount += 1
        if devicecount > maxcount: break

        tempURL = URL
        # Node
        if node !='Node':
            tempURL = tempURL+"/node="  + node
        # Event
        if evt !='NA':
            tempURL = tempURL+"/data_event=" + evt
        # URL for getting this device's data
        tempURL = tempURL + '+' + deviceName
        if args_dict['debug']: print (tempURL)

        # Download device data to a string
        response = urlopen(tempURL)
        if response is None:
            if args_dict['debug']: print (tempURL+"\n begat no reponse.")
            continue

        str1 = response.read().decode('utf-8').split('\n')
        if str1.count('No values'): 
            if args_dict['debug']: print (tempURL+"\n "+str1)
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
                            deviceName: data1})
        if df.empty:
            df=dfloc
        else:
            df=df.merge(dfloc,how="outer",left_index=True,right_index=True)


    if args_dict['debug']:
        print(df)
        
    return df

def save_to_file(args_dict, df, nameoverride=''):
    if nameoverride !='':
        df.to_csv(nameoverride,header=True,index=False)
    else:
        outfilename   =   os.path.join(args_dict['outdir'],r'DataLogger_From_%s_to_%s.csv'%(args_dict['starttime'],args_dict['stoptime']))
        df.to_csv(outfilename,header=True,index=False)

        
def main():

    args_dict = {'debug':False, 'maxcount': 0, 'starttime':'', 'stoptime':'', 'outdir':'', 'paramlist':[]}
    parse_args(args_dict)

    df = fetch_data(args_dict)
    save_to_file(args_dict,df,'./DataLogger.csv')

if __name__ == "__main__":
    main()
