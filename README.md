<!--
Copyright (c) The SimpleFIN Team
See LICENSE for details.
-->
[![Build Status](https://travis-ci.org/simplefin/bank-access.png)](https://travis-ci.org/simplefin/bank-access)

This repository contains a collection of scripts that you can use to
programmatically get bank transaction information.  The scripts herein only
read data and do not change the financial state of a bank (such as doing a
transfer).

In this document, the following terms are used interchangeably:

- financial institution
- bank
- credit union



# Goal #

We want the banks to implement [SimpleFIN](http://simplefin.org),
so eventually we won't need this repository.  These scripts exist as a bridge
from banks which don't implement SimpleFIN to tools which expect SimpleFIN.  

Tell your bank you want SimpleFIN!

And please contribute a script for your banks!



# How to use this repo #

## If you see your bank listed ##

If you see your bank listed in the `inst` directory, clone this repo,
install any dependencies:

    pip install -r requirements.txt

Install `banka`:

    python setup.py install

then run the script like this:

    banka run inst/bankA.com/list-accounts

`banka run inst/bankA.com/list-accounts` is nearly equivalent to just doing
`inst/bankA.com/list-accounts` with the added benefit that sensitive data typed
in to the terminal is not shown.  If you aren't using a terminal to run this
script (e.g. you are spawning this from within another process), you can just
call `inst/bankA.com/list-accounts`


## If you don't see your bank listed ##

If you don't see your bank listed in the `inst` directory, please contribute
one!  Follow [CONTRIBUTING.md](CONTRIBUTING.md) and do these steps:

1. Fork this repo.

2. Make a directory for your institution, complete with an `_identity` file
   and `list-accounts` script. (See [Writing a Script][writing-a-script] below).

3. Submit a pull request.


# [writing-a-script]: Writing a Script #



# Methods of Bridging #

The method a script uses to bridge between a bank and SimpleFIN depends on
what the bank makes available.  In order of preference, try the following when
writing a script for this repository:

1. OFX Server

   If the bank provides an OFX service, there (XXX will be) are utility scripts
   that will make connecting to that bank very easy.

2. OFX file download

   If the bank allows users to download OFX files, there (XXX will be) are
   utility scripts that will make parsing those downloaded files easy.

3. Some other file format

   If the bank allows users to download files in formats other than OFX,
   it will probably be easier to parse those files than to scrape the page.

4. Scraping

   If the bank doesn't provide any of the above, but they have a web portal,
   write a script that scrapes the page for transaction/account information.

5. Horse and Buggy

   If the bank doesn't have a web portal, you will need to write a script that
   hires a horse and buggy (including rider) to go to the bank in person, with
   your credentials written on parchment*.  The script must wait for the horse,
   buggy (and rider) to return with a listing of account details (in the form
   of a JSON document).

   * in the event that further authentication is required, either horse, rider
   or buggy may use services available (such as a telegraph or pigeon) to
   contact the running script for the required information.


