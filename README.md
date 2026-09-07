# BM7 BlockHTTPDNS Multi-Format Generator

以 BlackMatrix7 `BlockHttpDNS` 为唯一上游，GitHub Actions 定时生成多套结果。

## 输出

- `output/adguardhome.txt`：AdGuard Home DNS 封锁规则
- `output/mosdns.txt`：MosDNS v5 `domain_set` 规则
- `output/quantumultx-rewrite.conf`：Quantumult X URL Rewrite 拒绝规则
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

## Quantumult X Rewrite

在线订阅：

```text
https://raw.githubusercontent.com/hfgj/bm7-blockhttpdns-multi/main/output/quantumultx-rewrite.conf
```

可加入 Quantumult X：

```ini
[rewrite_remote]
https://raw.githubusercontent.com/hfgj/bm7-blockhttpdns-multi/main/output/quantumultx-rewrite.conf, tag=BlockHTTPDNS-Rewrite, update-interval=86400, opt-parser=false, enabled=true
```

转换语义：

- BM7 `DOMAIN/HOST` → 对该精确域名生成 `^https?://... url reject`
- BM7 `DOMAIN-SUFFIX/HOST-SUFFIX` → 对该域及其子域生成 `^https?://... url reject`
- `IP-CIDR/IP-CIDR6` **不转换成 Rewrite**

注意：URL Rewrite 属于 HTTP(S) 应用层处理，不能与 Filter/CIDR Reject 完全等价。尤其 HTTPS 是否能命中还取决于 Quantumult X 对该连接可见的信息及 MITM 配置；本输出不会自动生成或扩大 `[mitm] hostname`。固定 IP HTTPDNS 仍应由原 Filter 规则或路由器侧 nftables 处理。

该输出主要用于：即使 Quantumult X 因 SSID 触发 `all_direct`，仍希望通过 Rewrite 层阻断可被 QX 识别到的域名型 HTTPDNS 请求。Bilibili 当前的 `http://httpdns.bilivideo.com/...` 属于可直接命中的明文 HTTP 场景。

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
