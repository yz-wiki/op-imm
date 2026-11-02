# ImmortalWrt x86_64 云编译（ImageBuilder）

用官方 ImageBuilder 在 GitHub Actions 上拼装 x86_64 固件：不编译源码、不使用 Docker，单次 8~20 分钟。
打包流程参考 [wukongdaily/ImmortalWrt-ImageBuilder](https://github.com/wukongdaily/ImmortalWrt-ImageBuilder)。

> **只有手动触发才会编译**：工作流仅保留 `workflow_dispatch`，push 代码不会自动开始构建。

核心设计：**插件全部从 workflow 里挪出来了**。日常只需要编辑 `config/packages.yml`，
改插件、换版本、接第三方源都在这个文件里完成，workflow 本身不用碰。

## 快速开始

1. 把本仓库推送到你的 GitHub（或直接 Fork）
2. 按需编辑 [`config/packages.yml`](config/packages.yml) —— 不改也能用默认配置
3. 仓库页 → **Actions** → **Build ImmortalWrt x86_64** → **Run workflow**，按需勾选参数
4. 构建完成后自动发布到 **Releases**，固定 tag `Autobuild-x86-64` 滚动更新

> 同一个 tag 会被反复覆盖，因此工作流按分支加了 `concurrency` 串行化：连续触发时排队执行，不会互删资产。

## 插件配置：config/packages.yml

整个文件分五段：

| 段落 | 作用 | 什么时候改 |
|---|---|---|
| `base` | 基础组件，每次构建都编入 | 想常驻的系统包 / 中文包 |
| `groups` | 分组插件（proxy / monitor / docker / nas / network / system） | 增删某类插件 |
| `extra` | 你的自定义补充，默认空 | 临时塞一两个包 |
| `github_releases` | 只在 GitHub Release 发布的插件 | 包不在任何仓库里时 |
| `feeds` | 第三方软件源（索引 + 公钥） | 需要一整个第三方源时 |

**规则很简单：**

- 每行一个包名，写的是 opkg/apk 的**包名**，不是文件名
- 以 `#` 开头 = 不编译；**把 `#` 删掉 = 参与编译**
- 以 `-` 开头 = 从固件里移除该包（如 `- "-dnsmasq"`，注意要加引号）
- **组没有开关**：组里只要还有一个未注释的包，这个组就启用；整组注释掉就关闭

文件里已经预置了大量常用插件、全部默认注释着。想用哪个就取消注释，不用查半天包名。
所有取消注释的包都已确认存在于 ImmortalWrt 官方源（`openwrt-24.10` 和 `openwrt-25.12` 两个分支都有）。

### 场景 1：启用一个预置插件

比如想要 Samba 共享：

```yaml
  nas:
    - luci-app-samba4
    - luci-i18n-samba4-zh-cn
```

把 `# nas:` 和下面每一行前面的 `# ` 删掉即可。

### 场景 2：加一个官方源里就有的插件

在 `extra` 里写包名：

```yaml
extra:
  - luci-app-lucky
  - luci-i18n-lucky-zh-cn
```

> `luci-app-lucky` 官方源里没有，需要额外加 feed 或走 release，见下面场景 4。

### 场景 3：控制版本

- `github_releases` 默认不写 `tag` = 永远取上游 **最新 release**
- 写死 `tag: v0.12.12` = 锁定该版本
- 官方源 / 第三方源里的包，版本由 feed 索引决定

### 场景 4：加一个只在 GitHub Release 发布的插件

```yaml
github_releases:
  - package: luci-app-something
    repo: owner/repo
    required: false
```

`required: true` 表示下不到就让构建失败；`false` 表示下不到只告警、从官方源兜底。

### 场景 5：接入第三方软件源

```yaml
feeds:
  - name: mysource
    apk:     https://example.com/{branch}/x86_64/mysource/packages.adb
    apk_key: https://example.com/public-key.pem
    ipk:     https://example.com/{branch}/x86_64/mysource
    ipk_key: https://example.com/key-build.pub
```

`{branch}` 会自动替换成 `openwrt-25.12` / `openwrt-24.10`。只支持一种包管理器就只写一边。
公钥文件名不用管：ipk 侧工作流会用 `usign -F` 算出指纹自动改名。

## 运行参数

| 参数 | 说明 |
|---|---|
| 版本 | `24.10.6`（ipk/opkg）、`25.12.2 / 25.12.1 / 25.12.0`（apk） |
| 后台地址 | 首次开机应用的 LAN IP（默认 `10.10.1.1`） |
| **软件包空间** | 文本框，可填 `2G` / `3G` / `4G` / `2048` / `2048M`，范围 64~16384 MB |
| img 文件系统 | `both`（squashfs + ext4）/ `squashfs`（可恢复出厂）/ `ext4`（可离线扩容） |
| **固件格式** | 六个勾选框：**img（默认勾选）**、iso、qcow2、vmdk、vdi、vhdx，勾几个出几个 |
| PPPoE 账号 / 密码 | 两个输入框，**同时填写**才会把 WAN 设成 PPPoE 拨号；留空或只填一个 = WAN 用 DHCP |
| 代理 / 监控 / Docker | **没有开关**，由 `config/packages.yml` 的分组决定 |

## 内置插件（默认启用）

| 插件 | 25.12 | 24.10 | 来源 |
|---|---|---|---|
| OpenClash | ✅ | ✅ | 优先 GitHub 最新 release，失败回退官方源 |
| nikki | ✅ | ✅ | [nikkinikki feed](https://github.com/nikkinikki-org/OpenWrt-nikki)（含签名密钥） |
| momo | ✅ | ✅ | [momo feed](https://github.com/nikkinikki-org/OpenWrt-momo) |
| Homeproxy | ✅ | ✅ | ImmortalWrt 官方源 |
| sing-box | ✅ | ✅ | ImmortalWrt 官方源 |
| **bandix 后端** | ✅ | ✅ | [timsaya/openwrt-bandix](https://github.com/timsaya/openwrt-bandix/releases) |
| **bandix 前端（LuCI）** | ✅ | ✅ | [timsaya/luci-app-bandix](https://github.com/timsaya/luci-app-bandix/releases) |
| argon + argon-config | ✅ | ✅ | 官方源 + [jerrykuku/luci-theme-argon](https://github.com/jerrykuku/luci-theme-argon) |

> **bandix 前后端是两个仓库**：`openwrt-bandix` 只有后端采集服务（`bandix` 包），
> LuCI 界面在 `luci-app-bandix` 仓库。两个都要装，否则只有后台服务没有界面。
> 需要多网口支持可以用 `luci-app-bandix-plus`（已在配置文件里用注释预留）。

mihomo 内核与 GeoData **不预制**，装完在 OpenClash 里一键下载/更新。
nikki / momo 的代理内核同样在插件内按需下载（feed 只含 LuCI 与后端程序包）。

## 注意事项

- **多代理插件共存**：同时安装只是预置，**同一时间只能有一个接管流量**，其余在 LuCI 里停用。
- **PPPoE**：默认保留 `ppp` / `ppp-mod-pppoe`，WAN 默认 DHCP；两项账号密码都填才会预置拨号配置。
- **ISO 格式**对 rootfs 大小有额外限制，`4G` + `iso` 可能失败，建议先用 `2G`。
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
