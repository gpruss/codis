#!/my/path/to/CODiS/venv/bin/python

"""
This Python script downloads weather data that have been published by the
Taiwanese Central Weather Bureau (CWB) on it's Observation Data Inquire System
(CODiS). The data are formatted and station-wise written into comma separated
files. If the script comes across an existing station file, it will check the
last observation and continue the download from there.

Please see https://github.com/gpruss/codis for further information.
"""



################################### MODULES ####################################
# standard library
import sys
from datetime     import date, datetime, timedelta
from json         import load, JSONDecodeError
from os           import makedirs, path
from textwrap     import fill
from urllib.parse import quote

# third party libraries
from pandas       import ( DataFrame, MultiIndex, Timestamp, date_range,
                           read_html, to_datetime )

############################# FUNCTION DEFINITIONS #############################
def term_print(text, line_width = 80):
    """
    Print strings with a predefined line width.
    """
    for paragraph in str.splitlines(text):
        print(fill(paragraph, width = line_width))


########################### READ CONFIGURATION FILE ############################
# JSON files (JavaScript Object Notation) are easy to read and the json-module
# is part of the Python Standard library. To facilitate code maintenance with
# git all user configuration is transfered to the file './config.json'.

# get script directory
script_directory = path.dirname(path.realpath(__file__))


# indicate progress
# display a header consisting of the current date padded with hyphens
term_print(('\n{:-^80}'.format(datetime.now().strftime('%Y-%m-%d %H:%M'))))

# read the configuration file (returns a dictionary)
try:
    with open(path.join(script_directory, 'config.json')) as config_file:
            config = load(config_file)

    # indicate progress
    term_print('Reading configuration file:')

except FileNotFoundError:
    err_message = ('\nError: configuration file missing!\n\nCreate a file '
                   'called config.json in {} and specify (at least) the '
                   'stations to be downloaded. For further details see: '
                   'https://github.com/gpruss/codis.'
                  ).format(script_directory)
    term_print(err_message)
    sys.exit(1)

except JSONDecodeError as e:

    # create error message
    err_message = ('Error: invalid configuration file config.json\n\nPython '
                   'is unable to parse your configuration file:\n{}'
                  ).format(e)

    # display error message
    term_print(err_message)

    # cancel script execution
    sys.exit(1)


# get the data_directory
if 'data_directory' in config:
    data_directory = config['data_directory']

else:
    # if no data directory has been specified, default to
    # '/my/path/to/CODiS/data/'
    data_directory = path.join( script_directory, 'data')

# indicate progress
print( '> data directory:', data_directory)


# get the start date
# If no start date has been specified, default to January 1, 2010, because
# there are no older observation data available at CODiS than that!
# note: If data files are already present start_date will be overridden later
#       by the last observation of the file, i.e. the download will be con-
#       tinued!
if 'start_date' in config:

    try:

        # convert string into a date object
        start_date = datetime.strptime(config['start_date'], '%Y-%m-%d').date()

    except ValueError:

        # create error message
        err_message = ('\nError: start_date given in unknown format ({})\n\n'
                       'Please edit your config.json and use the following '
                       'date format: "YYYY-MM-DD", e.g. "2010-01-01"!'
                      ).format(config["start_date"])

        # display error message
        term_print(err_message)

        # cancel script execution
        sys.exit(1)


    # sanity check: start_date must not be prior to 2010-01-01
    if start_date < date(2010,1,1):

        # create error message
        err_message = ('\nError: start_date out of bounds ({})\n\nPlease edit '
                       'your config.json and choose a start_date that is not '
                       'earlier than January 1, 2010.').format(start_date)

        # display error message
        term_print(err_message)

        # cancel script execution
        sys.exit(1)

    # sanity check: start_date must not be later than the day before yesterday
    # note: see end_date for details
    if start_date > (date.today() - timedelta(days=2)):

        # create error message
        err_message = ('\nError: start_date out of bounds ({})\n\nPlease edit '
                       'your config.json and choose a start_date that is not '
                       'later than the day before yesterday (CODiS updates '
                       'are not that fast).').format(start_date)

        # display error message
        term_print(err_message)

        # cancel script execution
        sys.exit(1)

else:

    # set the default value
    start_date = date(2010,1,1)

# indicate progress
print( '> start date    :', start_date)


# get the end date
# If no end date has been specified, default to the day before yesterday,
# because data are updated at 12:00 noon. Therefore using the day before
# yesterday, i.e. date.today() - timedelta(days=2), should be safe regardless
# of the local time.
if 'end_date' in config:

    try:

        # convert string into a date object
        end_date = datetime.strptime(config['end_date'], '%Y-%m-%d').date()

    except ValueError:

        # create error message
        err_message = ('\nError: end_date given in unknown format ({})\n\n'
                       'Please edit your config.json and use the following '
                       'date format: "YYYY-MM-DD", e.g. "2017-01-01"!'
                      ).format(config["end_date"])

        # display error message
        term_print(err_message)

        # cancel script execution
        sys.exit(1)


    # sanity check: end_date must not be later than the day before yesterday
    if end_date > (date.today() - timedelta(days=2)):

        # create error message
        err_message = ('\nError: end_date out of bounds ({})\n\nPlease edit your '
                       'config.json and choose an end_date that is not later '
                       'than the day before yesterday (CODiS updates are not '
                       'that fast).').format(end_date)

        # display error message
        term_print(err_message)

        # cancel script execution
        sys.exit(1)

else:

    # set the default value
    end_date   = date.today() - timedelta(days=2)

# indicate progress
print( '> end date      :', end_date)


# sanity check: end_date must be after start_date
if start_date > end_date:

    term_print(('\nError: start_date ({}) is after end_date ({}).'
               ).format(start_date,end_date))

    # present the choice to swap or to quit
    user_input = input('Do you want to ...\n[s] swap the values, or\n'
                       '[q] quit the program?\n')

    # repeat until a valid input has been given
    while True:

        # user decides to swap the values of start_date and end_date
        if (user_input.lower() == 's') or (user_input.lower() == '[s]'):

            start_date, end_date = end_date, start_date

            # exit the loop
            break

        # user decides to quit the program
        elif (user_input.lower() == 'q') or (user_input.lower() == '[q]'):

            quit()

        # user does something different
        else:

            # input not recognized
            user_input = input( ('Input not recognized. Please type either [s]'
                                 ' to switch, or [q] to quit. ') )


# get the station list
if 'station_list' in config:

    station_list = config['station_list']

    if len(station_list) < 1:

        # create error message
        err_message = ('\nError: station_list is empty\n\nPlease edit your '
                       'config.json and add all stations to be downloaded:\n'
                       '"station_list" : {'
                       '\n    "[file_1]" : {"station" : "[ID_1]", "stname" : '
                       '"[hanzi_name_1]"},\n    "[file_2]" : {"station" : "[ID_2]"'
                       ', "stname" : "[hanzi_name_2]"},\n    ...\n    "[file_n]" :'
                       ' {"station" : "[ID_n]", "stname" : "[hanzi_name_n]"},\n }'
                      )

        # display error message
        term_print(err_message)

        # cancel script execution
        sys.exit(1)

else:

    # create error message
    err_message = ('\nError: station_list not defined\n\nPlease edit your '
                   'config.json and add all stations to be downloaded:\n'
                   '"station_list" : {'
                   '\n    "[file_1]" : {"station" : "[ID_1]", "stname" : '
                   '"[hanzi_name_1]"},\n    "[file_2]" : {"station" : "[ID_2]"'
                   ', "stname" : "[hanzi_name_2]"},\n    ...\n    "[file_n]" :'
                   ' {"station" : "[ID_n]", "stname" : "[hanzi_name_n]"},\n }'
                  )

    # display error message
    term_print(err_message)

    # cancel script execution
    sys.exit(1)


##################################### MAIN #####################################
# set CODiS base URL (CWB Observation Data Inquire System, CWB = Central Weather
# Bureau)
base_URL = ( 'http://e-service.cwb.gov.tw/HistoryDataQuery/'
            'DayDataController.do?command=viewMain' )


# create the data directory if it does not exist yet
if not path.isdir( data_directory ):

    # indicate progress
    print('\ncreating data directory: {}'.format(data_directory))

    # create the directory
    makedirs( data_directory )


# loop over all stations in station_list
for key, value in station_list.items():

    # indicate progress
    print('\n' + key.upper() )

    # create output path
    output_path = path.join( data_directory,
                             '{}_{}.csv'.format(key, value['station']) )

    # check file exists
    if path.exists(output_path):

        # set parameters for the to_csv-method:
        # append to the existing file (do not overwrite)
        access_mode = 'a'

        # do not print a header
        write_header = False

        # fetch the last observation from the file without reading the whole
        # file
        with open(output_path,'rb') as f:

            # go to the second last byte of the file (just in case there is a
            # trailing line break)
            f.seek(-2,2)

            # search backwards for a line break
            while f.read(1) != b'\n':

                # step back by two positions (using f.read(1) above to check
                # for the line break always pushes the position another step
                # forward)
                f.seek(-2,1)

            # read the line
            lastObservation = f.readline().decode('utf-8')

        # extract the date, i.e. first column
        start_date = lastObservation.split(',')[0]

        # convert date from string to date object
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    else:

        # set parameters for the to_csv-method:
        # create a new file
        access_mode = 'w'

        # print a header
        write_header = True


    # create iterable date range
    period = date_range( start = start_date, end = end_date, freq = 'd' )

    # check download period: Continue with the next station if files are up to
    # date
    if len(period) == 0:

        # indicate progress
        print('File is already up to date. Proceeding with the next station!')

        # continue with the next station
        continue


    # create empty DataFrame
    df = DataFrame()

    # loop over all days within the period
    for day in period:

        # indicate progress
        print( '> fetching', day.strftime( '%Y-%m-%d' ) )

        # assemble URL
        full_URL = ( "{}&station={}&stname={}&datepicker={}".format(
                    base_URL, value['station'], quote(quote(value['stname'])),
                    day.strftime('%Y-%m-%d')) )

        # read html table into a temporary DataFrame:
        # > the table of interest is called 'MyTable'
        # > skip the (condensed) columns heading
        # > use the first row as header
        # > use the first column as index
        # > treat the following as NA values (see the readme at
        #   http://e-service.cwb.gov.tw/HistoryDataQuery/downloads/Readme.pdf)
        #   > 'X': instrument malfunction
        #   > 'V': wind with no mean wind direction
        #   > '/': status unknown
        # > replace the value of 'T', i.e. precipitation < 0.1mm ('trace'),
        #   by 0.05 (Kristen's choice)
        # > do not return a list of length one, but the DataFrame itself
        tmp = read_html( io         = full_URL,
                         attrs      = { 'id' : 'MyTable' },
                         encoding   = 'utf-8',
                         skiprows   = 1,
                         header     = 0,
                         index_col  = 0,
                         converters = { '降水量(mm)Precp' : lambda x: 0.05 if x=='T' else x },
                         na_values  = ['X','V','/'] )[0]

        # no observation data in this interval ( 本段時間區間內無觀測資料。)
        if len(tmp) == 0:

            # indicate progress
            print('  ! no data in this interval')

            # skip rest of the loop
            continue

        # indicate progress
        print( '  + formatting data' )

        # reformat the index by combining the current date and time
        tmp.index = to_datetime( tmp.index, unit = 'h',
                                 origin = Timestamp(day) )

        # split DateTimeIndex into date and time MultiIndex
        tmp.index = MultiIndex.from_arrays( [tmp.index.date, tmp.index.time],
                                            names = ['Date','Time'] )

        # rename columns
        tmp.rename( columns = {
            '測站氣壓(hPa)StnPres'          : 'station pressure [hPa]'   ,
            '海平面氣壓(hPa)SeaPres'        : 'sea level pressure [hPa]' ,
            '氣溫(℃)Temperature'            : 'temperature [°C]'         ,
            '露點溫度(℃)Td dew point'       : 'dew point [°C]'           ,
            '相對溼度(%)RH'                 : 'relative humidity [%]'    ,
            '風速(m/s)WS'                   : 'wind speed [m/s]'         ,
            '風向(360degree)WD'             : 'wind direction [360°]'    ,
            '最大陣風(m/s)WSGust'           : 'gust speed [m/s]'         ,
            '最大陣風風向(360degree)WDGust' : 'gust direction [360°]'    ,
            '降水量(mm)Precp'               : 'precipitation [mm]'       ,
            '降水時數(hr)PrecpHour'         : 'precipitation hours [h]'  ,
            '日照時數(hr)SunShine'          : 'sun shine hours [h]'      ,
            '全天空日射量(MJ/㎡)GloblRad'   : 'global radiation [MJ/m²]' ,
            '能見度(km)Visb'                : 'visibility [km]'          },
            inplace = True )

        # append working table to the DataFrame
        df = df.append( tmp, verify_integrity = True )


    # indicate progress
    print('> writing data to', output_path )

    # write DataFrame to file
    df.to_csv( output_path, mode = access_mode, header = write_header )

# indicate progress
print('\nDone!\n')
