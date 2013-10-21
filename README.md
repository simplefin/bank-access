<!--
Copyright (c) The SimpleFIN Team
See LICENSE for details.
-->

This repository contains a collection of scripts that can be used to
programmatically get bank transaction information.  The scripts herein:

1. Are read-only (they do not mutate the financial state of a bank).

2. Provide a consistent interface (see below).


In this document, the following terms are used interchangeably:

- financial institution
- bank
- credit union


# Goal #

The goal of this repository is to eventually not exist.  These scripts exist
as a bridge from banks which don't implement SimpleFIN to tools which
expect SimpleFIN.  It is our hope that eventually, all banks will implement
SimpleFIN, which will render this repository useless.

Please contribute a script for your banks!

And let your bank know that you want them to implement SimpleFIN!


# Script API #


The structure of this repository is as follows:

    util/
    inst/
        bankA/
            _identity
            list-accounts
        bankB/
            ...


- `util/` contains utility scripts that might be shared among bank access
  scripts such as scripts that connect to OFX servers.

- `inst/` contains a directory per known financial institution (bank,
  credit union, etc...)

- `inst/*/_identity` is an Identity File for the bank directory it lives in
  (see below).

- `inst/*/list-account` is a List Accounts Bank Access script (see below).


## Identity File ##

The Identity File is a simple YAML document that describes the institution.  A
sample Indentity File looks like this:

    ---
    name: The Big Bank of Money
    domain: thebigbankofmoney.com
    simplefin_url: https://sfin.thebigbankofmoney.com

The `name` and `domain` fields are required.  All others are optional.


## Properties common to all Bank Access scripts ##

These scripts do the work of connecting to a bank, authenticating as a
particular user and accessing some resource(s) from the bank.

1. All Bank Access scripts are user executable (i.e. `chmod u+x name-of-script`).

2. The scripts use I/O channels in the ways described below.

3. Scripts may be written in any language, though we'd prefer scripts in
   languages already present over new languages.




### stdin (IN, channel 0) ###

Information required by the script (including sensitive information such as
passwords, PINs and security question answers) are written to stdin as a JSON
string terminated by a newline (byte 0x0A), like this:

    <JSON string>\n

For example, to provide the string `"blue"` the following would be written to
stdin (note the double quotes):

    "blue"

Which is a string of these bytes (in hexadecimal):

    22 62 6C 75 65 22 0A

The unicode snowman character (&#x263A; U+2603) would be written like this:

    "\u2603"


Each item written to stdin should correspond to a question being written to
the auth channel (see below).



### stdout (OUT, channel 1) ###

For successful runs, the result of the script will be written to stdout.
For most scripts, this will be a JSON document.

In the case of an error exit code, the meaning of stdout is not defined.




### stderr (OUT, channel 2) ###

Standard error is used for logging and error messages.  The presence of data
on standard error does not necessarily mean that the script failed.  Failure
is determined by the exit code only.

The format of stderr is not defined.




### auth (OUT, channel 3) ###

In addition to the standard I/O channels, each Bank Access script may also
write to channel 3, which is used for authentication.  When, during the course
of connecting to a bank, a script requires information from the runner of the
script (such as a username, password, security question answer, etc...), the
script will write a JSON string followed by a newline (byte 0x0A) to channel 3
in the following format:

    <JSON key>\n

For example, if a username is required the script would write to channel 3
(note the double quotes):

    "Username"

Which is a string of these bytes (in hexadecimal):
    
    22 55 73 65 72 6E 61 6D 65 22 0A


To run a script with channel 3 redirected to stderr, do this:

    bash the_script 3>&2

Other languages also include mechanisms for running processes that write to
non-standard file descriptors.  Look it up for your language.

It is up to the script's author to determine how to write to a non-standard
channel.  Here are some common languages (send a pull request if you'd like
to submit more examples).

Bash:

    #!/bin/bash
    echo '"foo"' >&3

Python

    #!/usr/bin/python
    import os
    import json
    os.write(3, json.dumps('foo')+'\n')


## List Accounts ##

List Accounts scripts must be named `list-accounts` and do the work of getting
account transaction information.

### Output ###

`list-accounts` produces a JSON document which is *almost* a
[SimpleFIN Account Set](http://simplefin.org/protocol.html#account-set) (see
that document for field definitions).  The `list-accounts` script will lack an
`id` field in each [Account](http://simplefin.org/protocol.html#account), and
instead have an `_insecure_id` field which contains the bank's id for the
account.

Here's an example document:

    {
      "accounts": [
        {
          "org": {
            "domain": "mybank.com"
            "sfin-url": null
          },
          "_insecure_id": "9982739",
          "name": "Savings",
          "currency": "USD",
          "balance": "100.23",
          "available-balance": "75.23",
          "balance-as-of": "AO334",
          "last-transaction-posted": "2013-07-29T19:22:09.210",
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

### Input ###

In addition to the auth/stdin channel I/O, the script must accept the following
optional command-line arguments:

- `--start-date=YYYY-mm-dd[THH:MM:SS]`
  
  If provided, then include transactions starting on the given timestamp.

- `--end-date=YYYY-mm-dd[THH:MM:SS]`

  If provided, then include transactions before (but not including) the given
  timestamp.


### Authentication ###

It is required that the first piece of authentication asked for by the
`list-accounts` script be the username/account number.
