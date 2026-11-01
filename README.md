# ImmortalWrt x86_64 云编译（ImageBuilder）

构建逻辑参考 [wukongdaily/ImmortalWrt-ImageBuilder](https://github.com/wukongdaily/ImmortalWrt-ImageBuilder)（原生 runner 直跑 ImageBuilder，不使用 Docker），并做了插件源的强化。

不做全量源码编译，不使用 Docker，单次构建约 5~10 分钟。

## 使用方法

1. 把本目录推送到你的 GitHub 仓库
2. 仓库页 → **Actions** → **Build ImmortalWrt x86_64** → **Run workflow**
3. 按需选择参数后运行
4. 构建完成后自动发布到 **Releases**，固定 tag `Autobuild-x86-64` 滚动更新（Release 说明含后台地址与插件清单）

## 可选参数

| 参数 | 说明 |
|---|---|
| 选择luci版本 | `25.12.2 / 25.12.1 / 25.12.0`（apk 包管理）/ `24.10.6`（ipk 包管理）。**官方无 24.19 版本**，24.x 系列即 24.10.6 |
| 管理地址 | 写入 `files/etc/uci-defaults/99-custom.sh`，首次开机自动应用 LAN IP（默认 `10.10.1.1`） |
| 软件包空间 | 1G / 2G / 3G / 4G（映射 ROOTFS_PARTSIZE 1024~4096） |
| 固件格式 | both（默认全发布）/ squashfs（可恢复出厂）/ ext4（可离线扩容） |
| 内置 mihomo 内核 | 默认开启：最新 mihomo + GeoIP.dat / GeoSite.dat / Country.mmdb / ASN.mmdb 直接写进固件 |
| argon-config | 默认开启：argon 主题的可视化配置插件 |
| sing-box-easy | 默认关闭；**仅 24.10 (ipk) 可用**，25.12 (apk) 自动跳过 |
| 移除 PPP | 默认开启：固件不含 PPP/PPPoE，WAN 默认 DHCP |
| bandix 版本 | 默认 `v0.12.12`（[timsaya/openwrt-bandix](https://github.com/timsaya/openwrt-bandix/releases)） |

基础包清单（与 wukongdaily 版一致，两个版本源均已验证存在）：argon 主题 + argon-config、ttyd、文件管理器、diskman、firewall、package-manager 中文包、`openssh-sftp-server`、`curl`；固件默认中文界面（`luci-i18n-base-zh-cn`）。

## 内置插件一览

| 插件 | 25.12 | 24.10 | 来源 |
|---|---|---|---|
| OpenClash（追新，优先 GitHub 最新版，失败回退官方源） | ✅ | ✅ | 官方源 + [vernesong/OpenClash](https://github.com/vernesong/OpenClash/releases) |
| mihomo 内核 + GeoData 内置 | ✅ | ✅ | [MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo) + [meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat) |
| nikki | ✅ | ✅ | [nikkinikki 官方 feed](https://github.com/nikkinikki-org/OpenWrt-nikki)（含签名密钥） |
| momo | ✅ | ✅ | [nikkinikki 官方 feed](https://github.com/nikkinikki-org/OpenWrt-momo) |
| Homeproxy | ✅ | ✅ | ImmortalWrt 官方源 |
| bandix | ✅ | ✅ | [timsaya/openwrt-bandix](https://github.com/timsaya/openwrt-bandix) releases |
| argon + argon-config（中文） | ✅ | ✅ | 官方源 + [jerrykuku/luci-theme-argon](https://github.com/jerrykuku/luci-theme-argon) |
| sing-box-easy | ❌ 仅 ipk | ✅ | [SealinGp/sing-box-easy](https://github.com/SealinGp/sing-box-easy) |

固件默认中文界面（`luci-i18n-base-zh-cn`）。

## 注意事项

- **多代理插件共存**：OpenClash / nikki / momo / Homeproxy / sing-box-easy 同时安装仅为预置，**同一时间只能有一个插件接管流量**，其余请在 LuCI 中停用。
- **PPPoE**：固件已移除 PPP 组件（可在参数中关闭移除）。你的网络环境不使用 PPPoE，WAN 保持 DHCP 即可。
- **OpenClash 内核更新**：内置内核为构建时最新版，后续更新可在插件内在线升级；Geo 数据同理。
- nikki / momo 的代理内核在插件内按需下载（feed 只含 LuCI 与后端程序包）。
- Releases 产物含 `sha256sums.txt`，下载后建议校验。

## 目录结构

```
github/
└── .github/
    └── workflows/
        └── build-immortalwrt.yml   # 唯一的工作流文件
```
