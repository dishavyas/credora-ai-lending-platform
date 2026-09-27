from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
r=c.post('/api/auth/login',json={'email':'admin@credora.ai','password':'Admin@123'}); assert r.status_code==200,r.text
h={'Authorization':'Bearer '+r.json()['access_token']}
cust=c.post('/api/customers',headers=h,json={'full_name':'Demo Borrower','email':'borrower@example.com','phone':'9999999999','annual_income':900000,'employment_type':'Salaried'}); assert cust.status_code==200,cust.text
cid=cust.json()['id']; assert c.patch(f'/api/customers/{cid}/kyc',headers=h,json={'status':'Verified'}).status_code==200
loan=c.post('/api/applications',headers=h,json={'customer_id':cid,'product':'Personal Loan','amount':250000,'tenure_months':24,'purpose':'Education','credit_score':760,'monthly_debt':8000}); assert loan.status_code==200,loan.text
aid=loan.json()['id']
for typ,name in [('Bank Statement','bank.pdf'),('Payslip','payslip.pdf'),('Identity Document','id.pdf')]:
 d=c.post('/api/documents',headers=h,json={'application_id':aid,'document_type':typ,'file_name':name,'extracted_summary':'Synthetic test document'}); assert d.status_code==200,d.text
 assert c.patch(f"/api/documents/{d.json()['id']}/verify",headers=h,json={'status':'Verified'}).status_code==200
assert c.post(f'/api/risk/{aid}',headers=h).status_code==200
assert c.post(f'/api/underwriting/{aid}/brief',headers=h).status_code==200
assert c.post(f'/api/underwriting/{aid}/review',headers=h,json={'decision':'approve','note':'Synthetic smoke test approval'}).status_code==200
assert c.post(f'/api/notifications/{aid}',headers=h,json={'channel':'Email'}).status_code==200
print('PASS: auth -> customer -> KYC -> application -> documents -> risk -> AI brief -> human review -> notification')
