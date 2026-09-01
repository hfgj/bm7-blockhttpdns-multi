# BM7 BlockHTTPDNS Multi-Format Generator

以 BlackMatrix7 `BlockHttpDNS` 为唯一上游，GitHub Actions 定时生成三套结果。

## 输出

- `output/adguardhome.txt`：AdGuard Home DNS 封锁规则
- `output/mosdns.txt`：MosDNS v5 `domain_set` 规则
- `output/nftables.nft`：nftables IPv4/IPv6 IP 集合
- `output/ipv4.txt` / `output/ipv6.txt`：纯 CIDR 列表
- `output/unsupported.txt`：无法自动转换的上游规则
- `output/metadata.json`：生成统计

## AdGuard Home

在线订阅：

```text
https://raw.githubusercontent.com/hfgj/bm7-blockhttpdns-multi/main/output/adguardhome.txt
```

## MosDNS v5

在线规则：

```text
https://raw.githubusercontent.com/hfgj/bm7-blockhttpdns-multi/main/output/mosdns.txt
```

下载到本地后，例如：

```yaml
- tag: block_httpdns
  type: domain_set
  args:
    files:
      - "/etc/mosdns/rule/blockhttpdns.txt"
```

在 sequence 中：

```yaml
- matches:
    - qname $block_httpdns
  exec: reject 3
```

MosDNS 语义：
- BM7 `DOMAIN/HOST` → `full:` 精确匹配
- BM7 `DOMAIN-SUFFIX/HOST-SUFFIX` → `domain:` 域及其子域

## nftables

在线集合文件：

```text
https://raw.githubusercontent.com/hfgj/bm7-blockhttpdns-multi/main/output/nftables.nft
```

`output/nftables.nft` 只创建：

```text
table inet bm7_httpdns
  set httpdns_v4
  set httpdns_v6
```

**不会自动安装 DROP/REJECT 规则。** 这样不会擅自修改 OpenWrt/ImmortalWrt 的 fw4 链结构，后续应把这些集合接到现有防火墙链。

## 自动更新

每天北京时间约 11:17 自动拉取 BM7、重新生成并比较内容；只有发生变化时才 commit/push，也支持手动 `Run workflow`。
