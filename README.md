# Hawaii Budget Worksheets

This project aims to provide the Hawaii Budget Worksheets as CSV formatted files.

The [Hawaii State Legislature's "Legislative Information"](http://www.capitol.hawaii.gov/leginfo.aspx) website is a wonderful resource that publishes the Budget Worksheets in electronic format as the budget progresses through the legislative session.  Unforunately, the legislature's website only publishes the worksheets as a Portable Document Format (PDF) file.  This format makes it very difficult to perform quick analysis on the worksheets.

This project aims to remove that difficulty by converting the worksheets into to a Comma Separated Value (CSV) format file.  The resulting CSV file can be easily parsed by a spreadsheet program such as Microsoft Excel  or Google Sheets.

The `bin/` dir contians the python script used convert a Hawaii State Legislature Budget Worksheet formatted PDF file into a CSV formatted text file.

**Note:** *So far, this has only been tested on the [2016 HB1700 HD1 worksheet](http://www.capitol.hawaii.gov/session2016/worksheets/2016_HB1700_HD1_final.pdf).  It has not been verified to produce correct results.*

You can view the initial parsing results of the [2016 HB1700 HD1 Budget Worksheet in Google Sheets](http://hbws201601.cfh.link)

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
