# ImmortalWrt x86_64 云编译（ImageBuilder）

用官方 ImageBuilder 在 GitHub Actions 上拼装 x86_64 固件：不编译源码、不使用 Docker，单次 5~15 分钟。
打包流程参考 [wukongdaily/ImmortalWrt-ImageBuilder](https://github.com/wukongdaily/ImmortalWrt-ImageBuilder)。

> **只有手动触发才会编译**：工作流仅保留 `workflow_dispatch`，push 代码不会自动开始构建。

核心设计：**插件全部从 workflow 里挪出来了**。日常只需要编辑 `config/packages.yml`，
改插件、换版本、接第三方源都在这个文件里完成，workflow 本身不用碰。

## 快速开始

1. 把本仓库推送到你的 GitHub（或直接 Fork）
2. 按需编辑 [`config/packages.yml`](config/packages.yml) —— 不改也能用默认配置
3. 仓库页 → **Actions** → **Build ImmortalWrt x86_64** → **Run workflow**，按需勾选参数
4. 构建完成后自动发布到 **Releases**，固定 tag `Autobuild-x86-64` 滚动更新
   （Release 说明里带后台地址、包管理器、插件清单、校验和）

> 同一个 tag 会被反复覆盖，因此工作流按分支加了 `concurrency` 串行化：连续触发时排队执行，不会互删资产。

## 插件配置：config/packages.yml

整个文件分五段，从简单到复杂：

| 段落 | 作用 | 什么时候改 |
|---|---|---|
| `base` | 基础组件，每次构建都编入 | 想常驻的系统包 / 中文包 |
| `groups` | 分组插件，对应 Run workflow 页面的开关 | 增删某类插件（如代理、监控、Docker） |
| `extra` | 你的自定义补充，默认空 | 临时塞一两个包 |
| `github_releases` | 只在 GitHub Release 发布的插件 | 包不在任何仓库里时 |
| `feeds` | 第三方软件源（索引 + 公钥） | 需要一整个第三方源时 |

### 1. 加一个官方源里就有的插件

在 `extra` 里写包名即可：

```yaml
extra:
  - luci-app-lucky
  - luci-i18n-lucky-zh-cn
```

### 2. 增删某个分组里的插件

开关在 Run workflow 页面，内容在 `groups` 下。比如给 `proxy` 组再加一个插件，或者整个组不想要了就把组名下的条目删掉。
组名和开关的绑定关系是固定的：`proxy ←→ enable_proxy`、`monitor ←→ enable_monitor`、`docker ←→ enable_docker`。
**新增一个组**才需要在 workflow 里同步加一个 boolean 开关和一行环境变量。

### 3. 控制插件版本

- 默认（不写 `tag`）= 永远取上游 **最新 release**
- 写死 `tag: v0.12.12` = 锁定该版本
- 对于官方源 / 第三方源里的包，版本由 feed 仓库索引决定；要锁死就自己把包下载到别处再指定源

```yaml
github_releases:
  - package: bandix
    repo: timsaya/openwrt-bandix
    tag: v0.12.12        # 不写则跟随 latest
    required: true       # 下不到就构建失败；false = 告警并从官方源兜底
```

### 4. 加一个第三方软件源（带公钥）

在 `feeds` 末尾按格式抄一条，`{branch}` 会被替换成 `openwrt-25.12` / `openwrt-24.10`：

```yaml
feeds:
  - name: mysource
    apk:     https://example.com/{branch}/x86_64/mysource/packages.adb
    apk_key: https://example.com/public-key.pem
    ipk:     https://example.com/{branch}/x86_64/mysource
    ipk_key: https://example.com/key-build.pub
```

- 只支持 apk 或只支持 ipk 就只写另一边，另一边留空 = 该版本下不启用这个源
- **apk 源**：公钥文件名随意，apk 只比对内容
- **ipk 源**：opkg 用 usign **指纹**当文件名找公钥，所以公钥必须重命名成指纹——
  workflow 会自动 `usign -F -p` 算指纹再改名，你只管填 URL
- 仓库索引与公钥都对不上时，包里所有依赖它的插件都会装不上

### 5. 加一个只在 GitHub Release 发布的插件

```yaml
github_releases:
  - package: luci-app-something
    repo: owner/repo
    required: false
```

工作流会验证资产名：按 `x86_64` / `all` 架构以及当前包管理器（apk 或 ipk）挑选，并且兼容两种命名风格
（`foo_1.0_all.ipk` 和 `foo-1.0_all.apk`）。下载后统一做规范化：
apk 去掉 `_x86_64` / `_all` 后缀，并把版本号里 git 提交段的点号改成 `~`
（例如 `luci-i18n-bandix-zh-cn-26.300.03255.108369b-r5_all.apk` → `...26.300.03255~108369b-r5.apk`），
否则 25.12 的 apk 索引会认不出包。

## 运行参数

| 参数 | 说明 |
|---|---|
| 版本 | `24.10.6`（ipk/opkg）、`25.12.2 / 25.12.1 / 25.12.0`（apk） |
| 后台地址 | 写入 `files/etc/uci-defaults/99-custom.sh`，首次开机应用 LAN IP（默认 `10.10.1.1`） |
| 软件包空间 | 1G / 2G / 3G / 4G（映射 `ROOTFS_PARTSIZE` 1024~4096） |
| img 文件系统 | `both`（squashfs + ext4 都出）/ `squashfs`（可恢复出厂）/ `ext4`（可离线扩容） |
| 固件格式 | 默认 `img`；可多选：`img,iso,qcow2,vmdk,vdi,vhdx`，填 `all` = 全部 |
| 代理套件 | OpenClash / nikki / momo / Homeproxy / sing-box，默认开 |
| 流量监控 | bandix，默认开 |
| Docker | 默认关（体积大） |
| PPPoE 预置 | 勾选后填账号密码，首次开机自动把 WAN 设成 PPPoE 拨号 |
| 移除 PPP 组件 | 默认关；勾选 PPPoE 预置时不可同时开启（工作流会直接报错） |

## 内置插件

| 插件 | 25.12 | 24.10 | 来源 |
|---|---|---|---|
| OpenClash | ✅ | ✅ | 优先 GitHub 最新 release，失败回退官方源 |
| nikki | ✅ | ✅ | [nikkinikki feed](https://github.com/nikkinikki-org/OpenWrt-nikki)（含签名密钥） |
| momo | ✅ | ✅ | [momo feed](https://github.com/nikkinikki-org/OpenWrt-momo) |
| Homeproxy | ✅ | ✅ | ImmortalWrt 官方源 |
| bandix | ✅ | ✅ | [timsaya/openwrt-bandix](https://github.com/timsaya/openwrt-bandix/releases) |
| argon + argon-config | ✅ | ✅ | 官方源 + [jerrykuku/luci-theme-argon](https://github.com/jerrykuku/luci-theme-argon) |
| Docker + dockerman | ✅ | ✅ | 官方源（默认关闭） |

mihomo 内核与 GeoData **不预制**，装完在 OpenClash 里一键下载/更新。
nikki / momo 的代理内核同样在插件内按需下载（feed 只含 LuCI 与后端程序包）。

## 注意事项

- **多代理插件共存**：同时安装只是预置，**同一时间只能有一个接管流量**，其余在 LuCI 里停用。
- **PPPoE**：默认保留 `ppp` / `ppp-mod-pppoe`，WAN 默认 DHCP，随时可在 LuCI 改成拨号；
  确定不用拨号时把「移除 PPP 组件」打开可省几 MB。
- Releases 产物含 `sha256sums.txt`，下载后建议校验。

## 两个包管理器的差异（实现细节）

| | 25.12 (apk) | 24.10 (ipk) |
|---|---|---|
| 仓库文件 | `repositories`（一行一个 `packages.adb`） | `repositories.conf`（`src/gz <name> <url>`） |
| 公钥放置 | `keys/*.pem`，按目录扫描，文件名任意 | `keys/<usign 指纹>`，**文件名必须等于指纹** |
| 本地包命名 | 必须 `<name>-<version>.apk`：去 `_x86_64` / `_all`，提交段点号改 `~` | 保持上游原名 |

ipk 那行的坑值得记一笔：opkg 的验签程序 `scripts/opkg-key` 用 `usign -F -p` 算出的**指纹**当文件名去 `keys/` 里找公钥，
直接存成 `keys/nikki.pub` 会让所有第三方源验签失败、`opkg install` 报 "package mentioned in index not found"。
工作流已改为下载后按指纹重命名。

## 目录结构

```
├─ .github/workflows/build-immortalwrt.yml   # 构建流程（一般不用改）
├─ config/packages.yml                       # ★ 插件清单，日常只改这里
└─ scripts/
   ├─ plan.py            # 读 packages.yml + 开关，生成构建计划
   ├─ prune.py           # 剔除没下载成功的可选包
   └─ fix-apk-names.sh   # 规范化 apk 文件名（25.12 专用）
```
