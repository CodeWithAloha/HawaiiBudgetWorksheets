# Hawaii Budget Worksheets

This project contains the Hawaii Budget Worksheets as CSV formatted files.

The [Hawaii State Legislature's "Legislative Information"](http://www.capitol.hawaii.gov/leginfo.aspx) site is a wonderful resource that publishes the Budget Worksheets as the budget progresses through the legislative session.  Unforunately, the legislature only publishes the worksheets in the Portable Document Format (PDF).  This format makes it very difficult to perform analysis on the worksheets.

This project aims to remove that difficulty by providing the worksheets already converted into to a Comma Separated Value (CSV) format file.  These CSV files can be easily parsed by a spreadsheet program such as Microsoft Excel  or Google Sheets.

The `bin/` dir contians the [python script](bin/Hawaii_Legislature_Budget_Worksheet_Converter.py) used convert a Hawaii State Legislature Budget Worksheet formatted PDF file into a CSV formatted text file.

**Note:** *So far, the convertor scriot has only been marginally tested on the [2016 HB1700 HD1 worksheet](http://www.capitol.hawaii.gov/session2016/worksheets/2016_HB1700_HD1_final.pdf).*

You can view the initial parsing results of the [2016 HB1700 HD1 Budget Worksheet in Google Sheets](http://hbws201601.cfh.link)

## Disclaimer

**_There has been very little effort to ensure the information conained in this repository is accurate or current. The author(s), nor Code for Hawaii, nor Code for America warrants the accuracy, reliability, or timeliness of any information in this repository and shall not be held liable for any losses caused by reliance on the accuracy, reliability or timeliness of such information. Portions of the information may be incorrect or not current. Any person or entity that relies on any information obtained from this repository does so at their own risk._**

## Installation

* Only tested on Ubuntu 15.10
* `pdftotext` version >= `0.33.0` must be available in the path
* `sudo apt-get poppler-utils` will install it `pdftotext`
* `python3` is also required in the path

## Usage

`./bin/Hawaii_Legislature_Budget_Worksheet_Converter.py 2016/2016_HB1700_HD1_final.pdf > 2016/2016_HB1700_HD1_final.csv`

## History

2016-03-20: v0.0.1 completed parsing of entire worksheet, needs testing and validation of output

## Credits

Copyright 2016 McKay H Davis

## License

[GPL v3.0](LICENSE.md)
