#!/usr/bin/env python


# curl https://api.bondora.com/api/v1/account/investments -H "Content-type: application/json" -H "Accept: application/json" -H "Authorization: Bearer H0kFRXrr8xHQQZzm99CxEGU0S2JwyIzTue6U3GUHIRAmP8g7" | jq .




import requests
import re
import datetime
import json
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import time

def getReport(bearer, reportType, startDate, endDate):
    headers = {'Authorization': 'Bearer {}'.format(bearer), 'Content-Type': 'application/json', 'Accept': 'application/json'}
    payload = {"ReportType": reportType, "PeriodStart": startDate, "PeriodEnd": endDate}
    r = requests.post('https://api.bondora.com/api/v1/report/', data=json.dumps(payload), headers=headers)
    rj = r.json()
    reportId = rj['Payload']['ReportId']
    time.sleep(1)
    r = requests.get('https://api.bondora.com/api/v1/report/{}'.format(reportId), headers=headers)
    rj = r.json()
    r = requests.delete('https://api.bondora.com/api/v1/report/{}'.format(reportId), headers=headers)
    return rj



bearer = ''
with open('bearer.conf', 'r') as f:
    bearer = f.read()
    f.close()

bearer = re.sub('[^a-zA-Z0-9]' , '', bearer)

# curl https://api.bondora.com/api/v1/report -X POST -H "Content-type: application/json" -H "Accept: application/json" -H "Authorization: Bearer H0kFRXrr8xHQQZzm99CxEGU0S2JwyIzTue6U3GUHIRAmP8g7" --data '{"ReportType": "4", "PeriodStart": "2019-01-01T16:25:24.2921787+02:00", "PeriodEnd": "2019-03-25T16:25:24.2921787+02:00" }' | jq .

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


try:
    prep = sum([e['PrincipalRepayment'] for i, e in enumerate(repayments['Payload']['Result'])])
    irep = sum([e['InterestRepayment'] for i, e in enumerate(repayments['Payload']['Result'])])
    lfrep = sum([e['LateFeesRepayment'] for i, e in enumerate(repayments['Payload']['Result'])])
    print("Principal Repayments:   {: 10.2f}".format(prep))
    print("Interest Repayments:    {: 10.2f}".format(irep))
    print("Late Fees Repayments:   {: 10.2f}".format(lfrep))
except:
    print(repayments)


inv = [(datetime.datetime.strptime(e['PurchaseDate'][:19], dateParseInv), e['Amount']) for i, e in enumerate(invests['Payload']) if e['LoanStatusCode'] != 3]
#inv = [(datetime.datetime.strptime(e['PurchaseDate'][:19], dateParseInv), e['PurchasePrice']) for i, e in enumerate(invests['Payload']) if e['LoanStatusCode'] != 3]
rep = [(datetime.datetime.strptime(e['Date'], dateParse), -e['PrincipalRepayment']) for e in repayments['Payload']['Result']]
inv.extend(rep)
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

acst = ([datetime.datetime.strptime(startDate, dateFormat)] , [0.0])
for i, e in enumerate(accountstatements['Payload']['Result']):
    acst[0].append(datetime.datetime.strptime(e['TransferDate'], dateParse))
    acst[1].append(e['BalanceAfterPayment'])
    #acst[1].append(acst[1][-1] + e['Amount'])



fig, ax = plt.subplots()



ax.plot_date(inrep[0], inrep[1], 'b-')
ax.plot_date(acst[0], acst[1], 'r-')
ax.plot_date(invi[0], invi[1], 'g-')
ax.set(xlabel='date', ylabel='EUR', title='My Bondora earnings')
ax.grid()

fig.autofmt_xdate()
fig.savefig("test.png")
plt.show()

