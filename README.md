# CODiS Download Tool
This Python script downloads weather data that have been published by the
Taiwanese Central Weather Bureau (CWB) on it's Observation Data Inquire System
(CODiS). The data are formatted and station-wise written into comma separated
files. If the script comes across an existing station file, it will check the
last observation and continue the download from there.

What the script does NOT do:

* rearrange lines to achieve a chronological order
* integrity checks (duplicate lines, uncovered time periods, etc.)


## Installation
If not present yet, install `Python3` (including `pip3`) and `git` on your
system. Please consult your system administrator, see your system
documentation and/or:

* https://www.python.org/downloads/
* https://git-scm.com/downloads

Create a working directory, initialize a git repository and fetch the source
code from github.com (the following sample code is meant to be run on Linux):

    $ mkdir -p ~/my/path/to/CODiS
    $ cd ~/my/path/to/CODiS
    $ git init
    $ git pull https://github.com/gpruss/codis

It is recommended (but not strictly necessary) to use a virtual environment for
dependency management and isolation (https://www.python.org/dev/peps/pep-0405/).
Python's venv module can be used to create such an environment (here
conveniently called 'venv'):

    $ python3 -m venv venv

Use your preferred text editor, e.g. `vim`, to to adjust the shebang, i.e. the
first line of the file which indicates the interpreter to be used. It needs to
point to the previously created virtual environment:
`#!/my/path/to/CODiS/venv/bin/python`

Activate the virtual environment, install the required modules and
deactivate it again:

    $ source venv/bin/activate
    $ pip install -r requirements.txt
    $ deactivate

The content of the data directory and the virtual environment should not be
placed under version control. Therefore the (default) directories 'data/' and
'venv/' are listed in the repository's .gitignore file. If you use different
directory names, make sure to adjust your .gitignore file:

    $ echo [name_of_my_environment]/ >> .gitignore
    $ echo [name_of_your_data_directory]/ >> .gitignore


## Usage
Create a configuration file called config.json. The only mandatory argument is
a list of the stations to be processed:

    {
        "station_list" : {
            "[file_name_1]" : { "station": "[ID_1]"}, "stname": "[hanzi_1]"},
            "[file_name_2]" : { "station": "[ID_2]"}, "stname": "[hanzi_2]"},
            ...
            "[file_name_n]" : { "station": "[ID_n]"}, "stname": "[hanzi_n]"}}
    }

Replace the (square) bracket expressions by actual values, e.g.:

    {
        "station_list" : {
            "Alishan" : { "station" : "467530", "stname" : "阿里山" },
            "Zhushan" : { "station" : "C0I110", "stname" : "竹山"   }}
    }

Because there are a lot of people (and operating systems) that cannot read
Chinese characters (hanzi), the transcribed station name should be used as
file name (note that the file extension .csv will be automatically appended).

In addition the following parameters may be specified:

* "data_directory": directory where files will be written to, defaults to ./data

* "start_date"    : beginning of the download period, defaults to January 1,
                    2010 (will be overwritten if matching files are already
                    present in the data directory!)

* "end_date"      : end of the download period, defaults to the day before
                    yesterday


Example config.json:

    {
        "data_directory" : "/my/path/to/CODiS/downloads",
        "start_date"     : "2016-12-17",
        "end_date"       : "2017-07-02",
        "station_list"   : {
            "Alishan"         : { "station" : "467530", "stname" : "阿里山"   },
            "Zhushan"         : { "station" : "C0I110", "stname" : "竹山"     }}
    }

Execute the script:

    $ ./get_weather_data.py

You can run the script as a cronjob, i.e. on a regular basis, to keep the files
up to date. Modify you cron table with:

    $ crontab -e

Add the following line to execute the script each Monday at 2pm and redirect
ouput and errors into files:

    0 14 * * 1 my/path/to/CODiS/get_weather_data.py > CODiS.log 2> CODiS.err

## Changelog
* config.json added to separate configuration and implementation


## Todo
* check validity: station_list
* email notification on error
* add timezone information for file update (import pytz, something like
  datetime.datetime.now(tz=pytz.timezone('Asia/Taipei'))
* use database instead of flat files
