# PPTimer

A lifetime-free PowerPoint countdown timer software.

## 使用说明 / Usage

1. 软件不用安装，放置桌面点击即可运行。  
   No installation required; simply place on your desktop and click to run.

   默认工作倒计时为 7 分钟，休息倒计时为 5 分钟。
   The default work countdown is 7 minutes; the break countdown is 5 minutes.

2. `+` / `-` 或滚轮可按一分钟调整时间；暂停时按 `S` 或右键菜单可输入分钟或 `分:秒`（最多 99:59）。
   Use `+/-` or the scroll wheel to adjust by one minute; press `S` or use the context menu to set minutes or `mm:ss` (up to 99:59).

3. 点击 `R` 或按 `R` 可重置时间，保留自定义的秒数。
   Click `R` or press `R` to reset, preserving custom seconds.

4. PPT 全屏放映可自动倒计时。  
   Automatic countdown during full-screen PowerPoint presentation.

5. 点击时间可启动/暂停倒计时。  
   Click the time to start/pause the countdown.

6. 按 `Esc` 退出；在窗口空白处、时间或 `R` / `T` 上右键可选择「退出 Exit」。  
   Press `Esc` to exit, or right-click on an empty area, the time, or `R` / `T` to select "Exit".

7. 倒计时结束时窗口会闪烁提醒并切换工作/休息模式；是否自动退出全屏演示可在右键菜单中开关（默认关闭）。
   When the timer ends, the window flashes and switches work/break modes; auto-exit from full-screen presentations can be toggled in the context menu (off by default).

8. 点击 `T` 可切换主题（深色 / 浅色 / 蓝色 / 紫色 / 暖橙 / 薄荷）；默认蓝色，主题偏好会自动保存。右键菜单可切换置顶状态。
   Click `T` to choose from six themes (blue by default); the preference is saved automatically. Use the context menu to toggle always-on-top.

主程序面向 Windows（使用 Windows API 检测全屏窗口），源码入口为 `PPT-Timer.py`。自动检测的是前台全屏窗口，不仅限于 PPT。
The app targets Windows (using Windows APIs for full-screen detection) and runs from `PPT-Timer.py`. Automatic detection applies to any foreground full-screen window, not just PowerPoint.

## 自行打包 / Build

```bash
pip install -r requirements.txt
python build.py
```

打包后会生成 `dist/PPTimer.exe` 和 `PPTimer.zip`。

After building, `dist/PPTimer.exe` and `PPTimer.zip` will be generated.

## GitHub Actions 自动构建

推送到 `v*` tag 即可触发自动构建，产物为 `PPTimer.zip`：

```bash
git tag v1.2.0
git push origin v1.2.0
```

## 致谢 / Credits

Based on [sunnybluesea/PPT-Timer](https://github.com/sunnybluesea/PPT-Timer).
