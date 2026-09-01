#!/usr/bin/env python3
from __future__ import annotations
import ipaddress, json, urllib.request
from pathlib import Path

UPSTREAM="https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/BlockHttpDNS/BlockHttpDNS.list"
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output"
OUT.mkdir(parents=True, exist_ok=True)
UA="bm7-blockhttpdns-multi/1.0"

EXACT={"DOMAIN","HOST"}
SUFFIX={"DOMAIN-SUFFIX","HOST-SUFFIX"}
V4={"IP-CIDR"}
V6={"IP-CIDR6","IP6-CIDR"}

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.read().decode("utf-8")

def norm(d): return d.strip().lower().rstrip(".")
def agh(d): return f"||{d}^"

def main():
    src=fetch(UPSTREAM)
    agh_rules=set(); mosdns=set(); v4=set(); v6=set(); unsupported=[]
    exact_domains=set(); suffix_domains=set()

    for raw in src.splitlines():
        s=raw.strip()
        if not s or s.startswith("#"): continue
        p=[x.strip() for x in s.split(",")]
        if len(p)<2:
            unsupported.append(s); continue
        t,val=p[0].upper(),p[1]
        if t in EXACT:
            d=norm(val); exact_domains.add(d)
            agh_rules.add(agh(d)); mosdns.add(f"full:{d}")
        elif t in SUFFIX:
            d=norm(val); suffix_domains.add(d)
            agh_rules.add(agh(d)); mosdns.add(f"domain:{d}")
        elif t in V4:
            try:
                n=ipaddress.ip_network(val,strict=False)
                if n.version!=4: raise ValueError
                v4.add(n)
            except ValueError:
                unsupported.append(s)
        elif t in V6:
            try:
                n=ipaddress.ip_network(val,strict=False)
                if n.version!=6: raise ValueError
                v6.add(n)
            except ValueError:
                unsupported.append(s)
        else:
            unsupported.append(s)

    if "httpdns.bilivideo.com" not in exact_domains | suffix_domains:
        raise RuntimeError("Bilibili HTTPDNS rule disappeared upstream; aborting.")

    agh_rules=sorted(agh_rules)
    mosdns=sorted(mosdns)
    v4=sorted(v4,key=lambda n:(int(n.network_address),n.prefixlen))
    v6=sorted(v6,key=lambda n:(int(n.network_address),n.prefixlen))
    unsupported=sorted(set(unsupported))

    (OUT/"adguardhome.txt").write_text(
        "! Title: BM7 BlockHTTPDNS for AdGuard Home\n"
        "! Source: BlackMatrix7 ios_rule_script / BlockHttpDNS\n"
        f"! Upstream: {UPSTREAM}\n"
        "! Generated automatically by GitHub Actions.\n"
        "! Note: ||domain^ blocks the domain and its subdomains.\n\n"
        + "\n".join(agh_rules) + "\n", encoding="utf-8")

    (OUT/"mosdns.txt").write_text(
        "# Title: BM7 BlockHTTPDNS for MosDNS v5\n"
        "# DOMAIN/HOST -> full:\n"
        "# DOMAIN-SUFFIX/HOST-SUFFIX -> domain:\n\n"
        + "\n".join(mosdns) + "\n", encoding="utf-8")

    v4_e=",\n            ".join(str(n) for n in v4)
    v6_e=",\n            ".join(str(n) for n in v6)
    nft = """# BM7 BlockHTTPDNS nftables IP sets
# Creates sets only; no DROP/REJECT rules are installed.

table inet bm7_httpdns {
    set httpdns_v4 {
        type ipv4_addr
        flags interval
        elements = {
            %s
        }
    }

    set httpdns_v6 {
        type ipv6_addr
        flags interval
        elements = {
            %s
        }
    }
}
""" % (v4_e, v6_e)
    (OUT/"nftables.nft").write_text(nft, encoding="utf-8")
    (OUT/"ipv4.txt").write_text("\n".join(str(n) for n in v4)+("\n" if v4 else ""),encoding="utf-8")
    (OUT/"ipv6.txt").write_text("\n".join(str(n) for n in v6)+("\n" if v6 else ""),encoding="utf-8")

    if unsupported:
        (OUT/"unsupported.txt").write_text(
            "# Rules not converted automatically:\n\n"+"\n".join(unsupported)+"\n",
            encoding="utf-8")
    elif (OUT/"unsupported.txt").exists():
        (OUT/"unsupported.txt").unlink()

    meta={
        "upstream":UPSTREAM,
        "adguardhome_rule_count":len(agh_rules),
        "mosdns_rule_count":len(mosdns),
        "exact_domain_count":len(exact_domains),
        "suffix_domain_count":len(suffix_domains),
        "ipv4_network_count":len(v4),
        "ipv6_network_count":len(v6),
        "unsupported_count":len(unsupported),
    }
    (OUT/"metadata.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
