# PPTimer

[中文](#中文) | [English](#english)

## 中文

一款永久免费使用的 PowerPoint 倒计时软件。

### 下载与安装

在 [GitHub Releases](https://github.com/scsagentclub/PPTimer/releases) 下载构建产物：

- `PPTimer.zip`：免安装版，解压后运行 `PPTimer.exe`。
- `PPTimer-1.2.0-win64.msi`：Windows 64 位安装版，安装到当前用户目录并创建开始菜单快捷方式，可在 Windows 设置中卸载。

### 使用说明

1. 软件不用安装，放置桌面点击即可运行。默认工作倒计时为 7 分钟，休息倒计时为 5 分钟。
2. `+` / `-` 或滚轮可按一分钟调整时间；暂停时按 `S` 或右键菜单可输入分钟或 `分:秒`（最多 99:59）。
3. 点击 `R` 或按 `R` 可重置时间，保留自定义的秒数。
4. PPT 全屏放映可自动倒计时。
5. 点击时间可启动/暂停倒计时。
6. 按 `Esc` 退出；在窗口空白处、时间或 `R` / `T` 上右键可选择「退出 Exit」。
7. 倒计时结束时窗口会闪烁提醒并切换工作/休息模式；是否自动退出全屏演示可在右键菜单中开关（默认关闭）。
8. 点击 `T` 可切换主题（深色 / 浅色 / 蓝色 / 紫色 / 暖橙 / 薄荷）；默认蓝色，主题偏好会自动保存。右键菜单可切换置顶状态。

主程序面向 Windows（使用 Windows API 检测全屏窗口），源码入口为 `PPT-Timer.py`。自动检测的是前台全屏窗口，不仅限于 PPT。

### 自行打包

```bash
pip install -r requirements.txt
python build.py
```

打包后会生成 `dist/PPTimer.exe` 和 `PPTimer.zip`。

生成 MSI 需要在 Windows 上安装 .NET 8 SDK，并在 PowerShell 中执行：

```powershell
dotnet tool install --global wix --version 5.0.2
./installer/build-msi.ps1
```

安装包版本读取自 `VERSION`，产物为 `dist/PPTimer-1.2.0-win64.msi`。

### GitHub Actions 自动构建

推送与 `VERSION` 一致的 `v*` tag 即可触发自动构建。例如 `VERSION` 为 `1.2.0` 时：

```bash
git tag v1.2.0
git push origin v1.2.0
```

工作流会生成 ZIP 和 MSI，验证 MSI 安装及卸载后，将两种产物上传到对应版本的 GitHub Release。也可在 Actions 页面手动运行工作流，下载构建产物。

给已有的 v1.2.0 补建 MSI：在 Actions 中选择 **Build Windows ZIP and MSI**，点击 **Run workflow**，选择 `main` 分支并填写 `release_tag` 为 `v1.2.0`。工作流会下载已有 Release 的 ZIP，用其中的 EXE 生成 MSI，并将安装包添加到该 Release。

### 致谢

基于 [sunnybluesea/PPT-Timer](https://github.com/sunnybluesea/PPT-Timer) 开发。

## English

A free-for-life PowerPoint countdown timer.

### Download and install

Download build outputs from [GitHub Releases](https://github.com/scsagentclub/PPTimer/releases):

- `PPTimer.zip`: portable edition. Extract the ZIP and run `PPTimer.exe`.
- `PPTimer-1.2.0-win64.msi`: Windows 64-bit installer. Installs for the current user, creates a Start menu shortcut, and supports uninstalling from Windows Settings.

### Usage

1. No installation required; simply place on your desktop and click to run. The default work countdown is 7 minutes; the break countdown is 5 minutes.
2. Use `+` / `-` or the scroll wheel to adjust by one minute. While paused, press `S` or use the context menu to enter minutes or `mm:ss` (up to 99:59).
3. Click `R` or press `R` to reset, preserving custom seconds.
4. The countdown starts automatically during full-screen PowerPoint presentations.
5. Click the time to start or pause the countdown.
6. Press `Esc` to exit, or right-click on an empty area, the time, or `R` / `T` to select "Exit".
7. When the timer ends, the window flashes and switches between work and break modes. Auto-exit from full-screen presentations can be toggled in the context menu (off by default).
8. Click `T` to choose from six themes: Dark, Light, Blue, Purple, Warm Orange, and Mint. Blue is the default, and your theme preference is saved automatically. Use the context menu to toggle always-on-top.

The app targets Windows and uses Windows APIs for full-screen detection. The source entry point is `PPT-Timer.py`. Automatic detection applies to any foreground full-screen window, not just PowerPoint.

### Build

```bash
pip install -r requirements.txt
python build.py
```

After building, `dist/PPTimer.exe` and `PPTimer.zip` will be generated.

To create the MSI, install the .NET 8 SDK on Windows and run these commands in PowerShell:

```powershell
dotnet tool install --global wix --version 5.0.2
./installer/build-msi.ps1
```

The installer version is read from `VERSION`. The output is `dist/PPTimer-1.2.0-win64.msi`.

### GitHub Actions automated builds

Push a `v*` tag matching `VERSION` to trigger an automated build. For example, when `VERSION` is `1.2.0`:

```bash
git tag v1.2.0
git push origin v1.2.0
```

The workflow builds the ZIP and MSI, verifies MSI installation and uninstallation, and uploads both outputs to the corresponding GitHub Release. You can also run the workflow manually from the Actions page and download its build artifacts.

To add an MSI to the existing v1.2.0 release, select **Build Windows ZIP and MSI** in Actions, click **Run workflow**, select the `main` branch, and set `release_tag` to `v1.2.0`. The workflow downloads the existing release ZIP, packages its EXE as an MSI, and attaches the installer to that release.

### Credits

Based on [sunnybluesea/PPT-Timer](https://github.com/sunnybluesea/PPT-Timer).
