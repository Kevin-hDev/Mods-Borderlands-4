# Mod Settings

在《无主之地 4》的暂停菜单和主菜单中加入的「模组」（MODS）菜单，采用游戏「选项」界面的设计，用来查看和修改《无主之地 4》Python SDK 的所有模组。

**ALPHA 版本**：这是第一个版本，尚未 100% 完成。它目前可以使用，但测试还不够充分，可能无法与所有模组配合。

已在游戏版本 **1.11.0-4906557**（Steam 版）上测试：单人模式，键盘、鼠标和手柄，安装了 22 到 29 个模组。从未在合作模式下或 Epic Games 版上试过。如果你遇到问题，请先查看[故障排除](TROUBLESHOOTING.zh.md)和[常见问题](FAQ.zh.md)，然后提交一个 issue，附上在重新启动游戏之前复制的日志文件 `...\Borderlands 4\OakGame\Binaries\Win64\Plugins\unrealsdk.log`（每次启动都会重写该文件）。

**与本仓库的其他内容不同，Mod Settings 采用 [Mozilla Public License 2.0 许可证](LICENSE)。**

## 功能

- 暂停菜单和主菜单中的「模组」入口会打开一个页面，包含检测到的所有 SDK 模组，该页面用游戏「选项」界面的组件构建。
- 每个模组都有自己的页面：设置分为标签页和子标签页，并显示所选设置的说明。模组允许时，可以开启或关闭它。
- 开关、滑块、左右箭头选择、下拉列表、按键和按钮，与 SDK 控制台的模组菜单相同。要更改按键，点击它，再按下新按键；按 Esc 取消。
- 更改会立即保存，滑块除外：滑块在关闭「模组」时，或下一次更改其他设置时保存。由 SDK 自己保存到 `...\Borderlands 4\sdk_mods\settings\`。
- 「模组」的文字跟随游戏语言：英语、法语或简体中文，其他语言显示英语。设置的名称和说明保持各模组提供的原样。

## 致模组作者

你无需在代码中添加任何东西：「模组」显示你的模组通过 `mods_base` 声明的选项，与控制台的模组菜单相同。每种选项如何显示、如何把选项整理成标签页，以及限制：见[模组作者指南](MOD_AUTHORS.zh.md)，另有[英文](MOD_AUTHORS.md)、[法文](MOD_AUTHORS.fr.md)和[日文](MOD_AUTHORS.ja.md)版本。

## 实现方式

更改设置时发生了什么，以及 Mod Settings 会改动哪些东西：见[工作原理](HOW_IT_WORKS.zh.md)。它分为两部分，都在这个文件夹中：

- `mod_settings/`：Python 包，以 `mod_settings.sdkmod` 发布。它读取 SDK 的模组和选项，并通过 `127.0.0.1` 上的本地服务提供给页面，该服务会拒绝来自网页的请求。每次更改都在游戏线程上执行。
- `page/`：页面的脚本和样式表，打包在 `mod-settings_999_P.pak` 中发布，同时附带加载它们的游戏暂停菜单和主菜单副本。`build_pak.py` 根据游戏最新的菜单生成这个资源包；`install_pak.py` 在游戏关闭时安装或移除它，并可随时检查它。`build_pak.py` 需要两个读写游戏资源包的外部工具；`install_pak.py` 需要 `deploy_sdkmods.py` 来获取游戏文件夹，并且只能在 Windows 上运行。这三个工具在 `game_tools.py` 中按作者工作环境中的位置指定：请把它们指向你自己的副本。该资源包含有游戏文件：它不在本仓库中，只在 Nexus 上提供。

## 安装

1. 安装[《无主之地 4》Python SDK](https://github.com/bl-sdk/oak2-mod-manager/releases/latest)。
2. 将 `mod_settings.sdkmod` 复制到 `...\Borderlands 4\sdk_mods\`。
3. 将 Nexus 文件「Mod Settings Paks」中的 `mod-settings_999_P.pak` 复制到 `...\Borderlands 4\OakGame\Content\Paks\`。两个文件都需要。
4. 启动游戏，打开暂停菜单或进入主菜单，然后选择「模组」。

要卸载，删除这两个文件即可。暂停菜单和主菜单会恢复原样，你其他模组的设置不会改变。

## 测试

在这个文件夹中分别运行每个测试：`python test_bridge.py`，页面则用 `node test_logic.js` 和 `node test_layout.js`。测试用假对象（`fixture_sdk.py`、`fixture_world.py`、`fixture_test_mod.py`）代替游戏的 SDK。每个测试输出一行 `RESULTAT:`，失败时以非零代码退出。选项类和保存功能来自 SDK，从已安装的 `mods_base.sdkmod` 中读取：把 `BL4_SDK_MODS` 设为你的 `...\Borderlands 4\sdk_mods` 文件夹路径，否则需要它的测试会显示 `SKIP`。`test_page_browser.py` 在无窗口的 Chrome 中，基于游戏的界面文件运行页面；如果 Chrome 不在 Windows 上的常用位置，或者没有从游戏资源包中读取这些文件的工具，它会显示 `SKIP`。

## 已知限制

- 在主菜单中，在「模组」里按 Esc 也会打开「退出游戏」窗口：点击「取消」，或使用「返回」和「关闭」。在暂停菜单中，Esc 正常工作。
- 有自己设置窗口的模组，在「模组」中只显示它向 SDK 声明的内容。
- Mod Settings 本身无法在「模组」中关闭：请使用 SDK 控制台（按 `~`，再输入 `mods`）。
- 其他替换游戏暂停菜单或主菜单的模组可能与它冲突。游戏更新可能改变这些菜单：如果更新后其中某个菜单表现异常，请先移除资源包，等待 Mod Settings 更新。

## 许可证

Mod Settings 采用 Mozilla Public License 2.0 许可证：见 [LICENSE](LICENSE) 或 <https://mozilla.org/MPL/2.0/>。如果你再分发修改过的文件，它们仍受 MPL-2.0 约束，其源代码必须保持可获取。如果你复用代码，请保留每个文件开头的声明：版权声明（`Copyright (c) 2026 kevin-hDev`）和许可证声明。资源包中的游戏文件属于 Gearbox Software 和 2K，不受本许可证约束。

这个想法来自 jackhumbert 为《赛博朋克 2077》制作的 Mod Settings。
