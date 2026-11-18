import csv,json,os
here=os.path.dirname(os.path.abspath(__file__));p=os.path.join(here,'..')
A=['BFF','GRI','EAR','LNK','LBF','OMA','AIA','CDR']
seg={a:{} for a in A};names={}
for r in csv.DictReader(open(p+'/nebraska_airports_monthly_2014_2026.csv')):
    k=r['reporting_month'][:7];a=r['origin_airport_code'];names[a]=r['origin_airport_name']
    f=lambda x:int(float(x or 0))
    seg[a][k]=dict(pax_dep=f(r['total_passengers']),seats=f(r['total_seats']),flights=f(r['total_departures']),freight=f(r['total_freight_lbs']))
arr={a:{} for a in A}
for r in csv.DictReader(open(p+'/nebraska_airports_monthly_arrivals_2014_2026.csv')):
    arr[r['airport']]['%s-%02d'%(r['year'],int(r['month']))]=int(r['arriving_passengers_market'])
months=sorted(seg['BFF'])
assert all(sorted(seg[a])==months for a in A)
out={'months':months,'names':{a:names[a] for a in A},'s':{}}
for a in A:
    out['s'][a]={m:[seg[a][k][m] for k in months] for m in ['pax_dep','seats','flights','freight']}
    out['s'][a]['pax_arr']=[arr[a].get(k,0) for k in months]
json.dump(out,open(os.path.join(here,'data.json'),'w'),separators=(',',':'))
print(len(months),months[0],months[-1])
