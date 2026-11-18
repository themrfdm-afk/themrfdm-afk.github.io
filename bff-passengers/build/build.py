import os
here=os.path.dirname(os.path.abspath(__file__));out=os.path.join(here,'..')
frag=open(os.path.join(here,'template.html')).read().replace('__DATA__',open(os.path.join(here,'data.json')).read())
open(os.path.join(out,'nebraska-explorer-embed.html'),'w').write(frag)
page='''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nebraska Air Travel Explorer</title>
<style>body{margin:0;padding:16px;background:#fff}</style>
</head><body>
'''+frag+'''
</body></html>
'''
open(os.path.join(out,'index.html'),'w').write(page)
print(len(frag)//1024,'KB')
