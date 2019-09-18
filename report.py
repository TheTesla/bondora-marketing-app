#!/usr/bin/env python



import requests
import re
import datetime
import json
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import time
import os



def getReport(bearer, reportType, startDate, endDate):
    headers = {'Authorization': 'Bearer {}'.format(bearer), 'Content-Type': 'application/json', 'Accept': 'application/json'}
    payload = {"ReportType": reportType, "PeriodStart": startDate, "PeriodEnd": endDate}
    r = requests.post('https://api.bondora.com/api/v1/report/', data=json.dumps(payload), headers=headers)
    rj = r.json()
    reportId = rj['Payload']['ReportId']
    time.sleep(100)
    r = requests.get('https://api.bondora.com/api/v1/report/{}'.format(reportId), headers=headers)
    rj = r.json()
    r = requests.delete('https://api.bondora.com/api/v1/report/{}'.format(reportId), headers=headers)
    return rj

here = os.path.dirname(os.path.realpath(__file__))

bearer = ''
with open(os.path.join(here, 'bearer.conf'), 'r') as f:
    bearer = f.read()
    f.close()

bearer = re.sub('[^a-zA-Z0-9]' , '', bearer)


headers = { 'Authorization': 'Bearer {}'.format(bearer),
            'Content-Type':  'application/json',
            'Accept':        'application/json' }

startDate = "2019-01-01T00:00:00.0000000+02:00"
dateFormat = "%Y-%m-%dT%H:%M:%S.0000000+02:00"
dateParse = "%Y-%m-%dT%H:%M:%S"
dateParseInv = "%Y-%m-%dT%H:%M:%S"
endDate = datetime.datetime.now().strftime(dateFormat)


r = requests.get('https://api.bondora.com/api/v1/account/investments', headers=headers)
invests = r.json()

time.sleep(3)

repayments = getReport(bearer, 4, startDate, endDate)
time.sleep(3)
accountstatements = getReport(bearer, 7, startDate, endDate)
time.sleep(3)
investments = getReport(bearer, 8, startDate, endDate)

invests = investments

try:
    prep = sum([e['PrincipalRepayment'] for i, e in enumerate(repayments['Payload']['Result'])])
    irep = sum([e['InterestRepayment'] for i, e in enumerate(repayments['Payload']['Result'])])
    lfrep = sum([e['LateFeesRepayment'] for i, e in enumerate(repayments['Payload']['Result'])])
    print("Principal Repayments:   {: 10.2f}".format(prep))
    print("Interest Repayments:    {: 10.2f}".format(irep))
    print("Late Fees Repayments:   {: 10.2f}".format(lfrep))
except:
    print(repayments)


#inv = [(datetime.datetime.strptime(e['PurchaseDate'][:19], dateParseInv), e['Amount']) for i, e in enumerate(invests['Payload']) if e['LoanStatusCode'] != 3]
inv = [(datetime.datetime.strptime(e['LoanDate'] if e['BoughtFromResale_Date'] is None else e['BoughtFromResale_Date'], dateParseInv), e['Amount']) for i, e in enumerate(invests['Payload']['Result'])]
#inv = [(datetime.datetime.strptime(e['LoanStatusActiveFrom'][:19], dateParseInv), e['Amount']) for i, e in enumerate(invests['Payload']['Result'])]
#inv = [(datetime.datetime.strptime(e['LoanStatusActiveFrom'][:19], dateParseInv), e['BidPrincipal']) for i, e in enumerate(invests['Payload']['Result'])]
#soldinv = [(datetime.datetime.strptime(e['SoldInResale_Date'][:19], dateParseInv), -e['Amount']) for i, e in enumerate(invests['Payload']['Result']) if e['SoldInResale_Price'] is not None]
soldinv = [(datetime.datetime.strptime(e['SoldInResale_Date'][:19], dateParseInv), -e['SoldInResale_Principal']) for i, e in enumerate(invests['Payload']['Result']) if e['SoldInResale_Price'] is not None]
#inv = [(datetime.datetime.strptime(e['PurchaseDate'][:19], dateParseInv), e['PurchasePrice']) for i, e in enumerate(invests['Payload']) if e['LoanStatusCode'] != 3]
rep = [(datetime.datetime.strptime(e['Date'], dateParse), -e['PrincipalRepayment']) for e in repayments['Payload']['Result']]
inv.extend(rep)
inv.extend(soldinv)
invs = sorted(inv, key=lambda x: x[0])

invi = ([datetime.datetime.strptime(startDate, dateFormat)] , [0.0])
for d, e in invs:
    invi[0].append(d)
    invi[1].append(invi[1][-1]+e)

print("Loan Amount:            {: 10.2f}".format(invi[1][-1]))

inrep = ([datetime.datetime.strptime(startDate, dateFormat)] , [0.0])
for i, e in enumerate(repayments['Payload']['Result']):
    inrep[0].append(datetime.datetime.strptime(e['Date'], dateParse))
    inrep[1].append(inrep[1][-1] + e['InterestRepayment'])

deposits = ([], [])
bonus = ([], [])
acst = ([datetime.datetime.strptime(startDate, dateFormat)] , [0.0])
for i, e in enumerate(accountstatements['Payload']['Result']):
    acst[0].append(datetime.datetime.strptime(e['TransferDate'], dateParse))
    acst[1].append(e['BalanceAfterPayment'])
    if 'TransferDeposit' in e['Description']:
        deposits[0].append(datetime.datetime.strptime(e['TransferDate'], dateParse))
        deposits[1].append(e['Amount'])
    elif 'TransferBonus' in e['Description']:
        bonus[0].append(datetime.datetime.strptime(e['TransferDate'], dateParse))
        bonus[1].append(e['Amount'])

    #acst[1].append(acst[1][-1] + e['Amount'])


fig, ax = plt.subplots()



ax.plot_date(inrep[0], inrep[1], 'b-', label='Interest')
ax.plot_date(acst[0], acst[1], 'r-', label='Balance')
ax.plot_date(invi[0], invi[1], 'g-', label='Investments')
ax.plot_date(deposits[0], deposits[1], 'yo', label='Deposits')
ax.plot_date(bonus[0], bonus[1], 'go', label='Commission')
ax.set(xlabel='date', ylabel='EUR', title='My Bondora earnings')
ax.legend(loc=0)
ax.grid()

fig.autofmt_xdate()
fig.savefig(os.path.join(here,'report.svg'))
#plt.show()

