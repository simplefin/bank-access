<!--
Copyright (c) The SimpleFIN Team
See LICENSE for details.
-->

The structure of this repository is as follows:

    banka/
    inst/
        bankA.com/
            _identity
            list-accounts
        bankB.com/
            ...


- `banka/` contains a Python library for code useful to all scripts
  such as scripts that connect to OFX servers or that parse OFX files.

- `inst/` contains a directory per known financial institution (bank,
  credit union, etc...).  Please use the domain name of the institution for
  the directory name where possible.

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

For example, to provide the string `blue` the following would be written to
stdin followed by a newline (note the double quotes):

    "blue"

Which is a string of these bytes (in hexadecimal):

    22 62 6C 75 65 22 0A

The unicode snowman character (&#x263A; U+2603) would be written like this:

    "\u2603"


Each item written to stdin corresponds to a question written to the auth
channel (see below), and each answer must be given in the same order that
the question was asked.



### stdout (OUT, channel 1) ###

For successful runs, the result of the script will be written to stdout.
For most scripts, this will be a JSON document.

In the case of an non-zero (error) exit code, the meaning of stdout is not
defined.




### stderr (OUT, channel 2) ###

Standard error is used for logging and error messages.  The presence of data
on standard error does not necessarily mean that the script failed.  Failure
is determined by the exit code only.

The format of stderr is not defined.




### control (OUT, channel 3) ###

If a script needs information from its parent (the thing that ran it or spawned
it) such as username, password, security question, etc. it would write a JSON
object followed by a newline (byte 0xA) to channel 3.  The object contains a
combination of the following attributes:

- `key` - **(required)** A unique identifier for this piece of information,
  such as `"password"` or `"PIN"`.  The keys `"_state"` and `"_login"`
  have special meaning.  `"_login"` must be the first piece of information
  requested by the script.  If the caller has no value for `"_state"` it should
  pass `null` in response to a request for `"_state"`. 
- `sensitive` - (optional) A `true` value indicates that the data asked for
  is sensitive.  Default: `true`
- `persistent` - (optional) A `true` value indicates that the data asked for
  is persistent and can be assumed to be the same from day to day.  For
  instance, a PIN is persistent because it doesn't change, but a one-time
  authorization token is not persistent.  Default: `true`
- `prompt` - (optional) A string prompt for the piece of data.  If not provided
  or if `null`, then the `key` will be used.  The `prompt` is a way to
  provide a human-readable name for a `key`.
- `value` - (optional) A JSON value for the given `key`.  The presence of a
  `value` attribute means that the caller should store the value for the given
  `key` for the next time the script is called.

**Important Note:** The first thing every script *must* ask for is the
account number or login name for the account.

For instance, a script may ask for the username by writing the following
to channel 3, followed by a newline:

    {"key":"_login", "prompt":"Username"}

Which is a string of these bytes (in hexadecimal):

    7B 22 6B 65 79 22 3A 22 5F 6C 6F 67 69 6E 22 2C 20 22 70 72 6F 6D 70 74 22 3A 22 55 73 65 72 6E 61 6D 65 22 7D 0A


#### Running ####

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

### Usage ###

The script must conform to this usage description:

    list-accounts [options]
    
    Options:

        --start-date=YYYY-mm-dd   If provided, include transactions starting
                                  on the given date.
        --end-date=YYYY-mm-dd     If provided, include transactions on or
                                  before the given date (XXX sure?)


### Authentication ###

It is required that the first piece of authentication asked for by the
`list-accounts` script be the username/account number.

