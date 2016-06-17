#!/usr/bin/env python
__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

import smtplib



def sendMail():
    to = 'd.moldovan@dsg.tuwien.ac.at'
    user = 'dmoldovan'
    password = 'IAmPeEichD@TU'
    smtpserver = smtplib.SMTP("mail.infosys.tuwien.ac.at",587)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo() # extra characters to permit edit
    smtpserver.login(user, password)
    header = 'To:' + to + '\n' + 'From:' + to + '\n' + 'Subject: [Run-Time Verification Platform][Test][Failure]' + 'TEST NAME' + '\n'
    print header
    msg = header + '\n this is test msg from health platform \n\n'
    smtpserver.sendmail(user, to, msg)
    print 'done!'
    smtpserver.close()


if __name__=='__main__':
    sendMail()