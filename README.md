<!--
Copyright (c) The SimpleFIN Team
See LICENSE for details.
-->

[![Build Status](https://travis-ci.org/simplefin/bank-access.png?branch=master)](https://travis-ci.org/simplefin/bank-access)

# THE Goal #

THE Goal of this project is self-destruction.  We would like to live in a world where this project doesn't need to exist.  But until the banks of the world implement a secure, standardized way to access financial data, a project such as this must exist to fill that gap.

Banks implementing [SimpleFIN](http://simplefin.org) is one way to achieve this goal.  But any secure, standardized method would suffice.

Tell your bank you want SimpleFIN!

And please contribute a script for your bank!



# What's in here? #

This repository contains a collection of scripts can be used to
programmatically get bank transaction information.  The scripts herein only read data and do not change the financial state of a bank (such as doing a transfer).

In this document, the following terms are used interchangeably:

- financial institution
- bank
- credit union



# How to use this repo #

Install (siloscript)[https://github.com/simplefin/siloscript]:

    pip install git+git://github.com/simplefin/siloscript.git@master

Run stuff

XXX



## If your bank isn't listed ##

If your bank isn't listed, please contribute!  Follow
[CONTRIBUTING.md](CONTRIBUTING.md) and these steps:

1. Fork this repo.

2. Make a directory for your bank with an `info.yml` file.  Name the
   directory the domain name of the bank, if possible.

3. Write a `list-accounts` script. (See [Writing a Script](#writing-a-script)).

4. Submit a pull request.



# `info.yml` file #

The `info.yml` file should have at least the following information:

    ---
    name: America First Credit Union
    domain: americafirst.com
    maintainers:
      - joe (joe@example.com)

`maintainers` is a list of people who are willing to maintain the scripts within the directory (i.e. test the scripts when the underlying library changes or fix them when the bank breaks them).  Include as much contact information as you feel comfortable sharing.  A URL to your Github profile would be fine.

The file may also contain other information as needed.



# Writing a Script #

How you write the script depends on what the bank provides.  In order of preference, try the following when writing a script:

1. OFX Server

   Check www.ofxhome.com to see if your bank provides an OFX server.  If so,
   writing a script is straightforward.  Use
   [`banka/inst/americafirst.com`](banka/inst/americafirst.com/) as a
   model.

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


## Output ##

If successful, the script should write a
[SimpleFIN Account Set](http://simplefin.org/protocol.html#account-set) to
stdout and exit with exit code `0`.  Here's an example:

    {
      "accounts": [
        {
          "org": {
            "domain": "mybank.com"
            "sfin-url": null
          },
          "id": "abcdef1234abc",
          "name": "Savings",
          "currency": "USD",
          "balance": "100.23",
          "available-balance": "75.23",
          "balance-as-of": "2013-07-29T19:22:09.210",
          "transactions": [
            {
              "id": "12394832938403",
              "posted": "1995-02-17T23:56:12.22239",
              "amount": "-33293.43",
              "description": "Uncle Frank's Bait Shop",
            }
          ]
        }
      ]
    }

Use stderr for logging.


## Development ##

Run your script with the credential wrapper:

    banka run <BANK DOMAIN>/list-accounts

If you are working out of the Git repo, without having installed the package,
you may need to do this instead:

    PYTHONPATH=. bin/banka run <BANK DOMAIN>/list-accounts

You may also find it helpful to store sensitive data to a local, encrypted
database during development.  See the `--store` option for more information:

    banka run --help


## Asking for credentials ##

Your script should prompt for credentials.  If you are writing a Python script,
prompt for credentials using `banka.prompt.prompt` like this:

    from banka.prompt import prompt
    username = prompt('_login')
    password_or_pin = prompt('password')

**All scripts must** prompt for the specially named `_login` credential
**first.**


## Saving state between runs ##

Your script may need to save state between each run (for instance, cookies
gathered during screen scraping).  Your script may ask for saved state using
`banka.prompt.prompt` as in [Asking for credentials](#asking-for-credentials):

    from banka.prompt import prompt
    state = prompt('_state', ask_human=False)

The script requests the parent to save the state with `banka.prompt.save`
like this:

    from banka.prompt import save
    save('_state', "some string of data that should be saved")


## Asking for account `id` ##

To fulfill [SimpleFIN's account id](http://simplefin.org/protocol.html#account.id)
requirement, ask for an alias instead of using the bank-provided id, like this:

    from banka.prompt import alias
    account1_alias = alias('account 1')
    account2_alias = alias('account 2')
