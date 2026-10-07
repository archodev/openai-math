import json, subprocess, os, concurrent.futures as cf
c=json.load(open('video/data/catalog.json'))
def job(e):
    p=e['papers'][0]['path'] if e['papers'] else None
    if not p or not os.path.exists(p): return e['num'], 'missing '+str(p)
    out=f"video/assets/thumbs/{e['num']}"
    if not os.path.exists(out+'.png'):
        subprocess.run(['pdftoppm','-f','1','-l','1','-png','-r','60','-singlefile',p,out],check=False)
    return e['num'], 'ok'
with cf.ThreadPoolExecutor(4) as ex:
    res=list(ex.map(job,c))
bad=[r for r in res if r[1]!='ok']
print(len(res), 'bad', bad)
