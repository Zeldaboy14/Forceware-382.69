#!/usr/bin/env python3
"""Reconstruct October19 from the exact published October17 package, offline.

No installer execution, driver installation, firmware flash or network access.
The earlier stock-input recipe remains available in rebuild.py.
"""
import argparse, datetime, hashlib, json, re, subprocess
from pathlib import Path
from rebuild import child, inventory, repack, require, run7z

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base-installer',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--sevenzip',default='7z')
    a=ap.parse_args();here=Path(__file__).resolve().parent
    m=json.loads((here/'sources/october19/manifest.json').read_text())
    original=a.base_installer.read_bytes()
    require(sha(original)==m['base_installer_sha256'],'Wrong October17 installer')
    root=a.out.resolve();require(not root.exists(),'Output directory already exists')
    root.mkdir(parents=True);work=root/'work';work.mkdir()
    package=root/'Forceware 382.69';cpl=work/'cpl'
    run7z(a.sevenzip,['x','-y','-o'+str(package),str(a.base_installer.resolve())],work/'extract-base.log')
    require(inventory(package)==m['base_package'],'Base package inventory differs')
    run7z(a.sevenzip,['x','-y','-o'+str(cpl),str(package/'Display.Driver/NvCplSetupInt.exe')],work/'extract-cpl.log')
    require(inventory(cpl)==m['base_cpl'],'Base Control Panel inventory differs')
    for r in m['changes']:
        require(r['tree'] in ['package','cpl'],'Unknown output tree')
        target=child(package if r['tree']=='package'else cpl,r['path'])
        b=target.read_bytes()if target.exists()else b''
        require(len(b)==r['original_bytes']and sha(b)==r['before_sha256'],'Patch input differs: '+r['path'])
        out=bytearray(b[:r['output_bytes']])
        for e in r['edits']:
            off=e['offset'];before=bytes.fromhex(e['before']);after=bytes.fromhex(e['after'])
            require(off>=0 and len(before)==len(after) and off+len(before)<=len(out),'Invalid patch bounds')
            require(out[off:off+len(before)]==before,'Patch byte guard failed: '+r['path'])
            out[off:off+len(before)]=after
        out.extend(bytes.fromhex(r['tail']))
        require(len(out)==r['output_bytes']and sha(out)==r['after_sha256'],'Patch output differs: '+r['path'])
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(out)
    require(inventory(cpl)==m['final_cpl'],'Final Control Panel payload differs')
    expected={k:v for k,v in m['final_package'].items()if k not in ['Display.Driver/NvCplSetupInt.exe','SHA256SUMS.txt']}
    require({k:v for k,v in inventory(package).items()if k in expected}==expected,'Final runtime payload differs')
    date=datetime.datetime.strptime(m['build_date'],'%m/%d/%Y').date()
    repack(a.sevenzip,(package/'Display.Driver/NvCplSetupInt.exe').read_bytes(),cpl,package/'Display.Driver/NvCplSetupInt.exe',work/'cpl.7z',work/'pack-cpl.log',build_date=date)
    checksums=package/'SHA256SUMS.txt';checksums.unlink()
    checksums.write_text(''.join(h+'  '+n+'\n'for n,h in sorted(inventory(package).items())))
    start=original.index(b';!@Install@!');end=original.index(b"7z\xbc\xaf\x27\x1c",start)
    cfg=re.sub(r'Forceware 382\.69[^"\r\n]*','Forceware 382.69',original[start:end].decode())
    launcher=original[:start]+cfg.encode()+original[end:];exe=root/(m['release_title']+'.exe')
    repack(a.sevenzip,launcher,package,exe,work/'package.7z',work/'pack.log',outer=True,release_title=m['release_title'],build_date=date)
    run7z(a.sevenzip,['x','-y','-o'+str(work/'package-check'),str(exe)],work/'check-package.log')
    run7z(a.sevenzip,['x','-y','-o'+str(work/'cpl-check'),str(package/'Display.Driver/NvCplSetupInt.exe')],work/'check-cpl.log')
    require(inventory(work/'package-check')==inventory(package),'Final installer extraction differs')
    require(inventory(work/'cpl-check')==m['final_cpl'],'Final nested installer extraction differs')
    require(set(inventory(package))==set(m['final_package']),'Unexpected package files')
    r=dict(runtime_payload_exact=True,exact_release_file_matches=len(expected),control_panel_file_matches=len(m['final_cpl']),outer_extraction_verified=True,nested_extraction_verified=True,installer_sha256=sha(exe.read_bytes()),release_installer_sha256=m['release_installer_sha256'],archive_hash_may_differ=True)
    (root/'rebuild-result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

if __name__=='__main__': main()
