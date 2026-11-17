# PPTimer

[中文](#中文) | [English](#english)

## 中文

一款永久免费使用的 PowerPoint 倒计时软件。

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

### GitHub Actions 自动构建

推送到 `v*` tag 即可触发自动构建，产物为 `PPTimer.zip`：

```bash
git tag v1.2.0
git push origin v1.2.0
```

### 致谢

基于 [sunnybluesea/PPT-Timer](https://github.com/sunnybluesea/PPT-Timer) 开发。

## English

A free-for-life PowerPoint countdown timer.

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

### GitHub Actions automated builds

Push a `v*` tag to trigger an automated build that produces `PPTimer.zip`:

```bash
git tag v1.2.0
git push origin v1.2.0
```

### Credits

Based on [sunnybluesea/PPT-Timer](https://github.com/sunnybluesea/PPT-Timer).
