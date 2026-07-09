# PPTimer

A lifetime-free PowerPoint countdown timer software.

## 使用说明 / Usage

1. 软件不用安装，放置桌面点击即可运行。  
   No installation required; simply place on your desktop and click to run.

2. `+` / `-` 或滚轮可调整时间。  
   Use the `+/-` keys or scroll wheel to adjust the time.

3. 点击 `R` 可重置时间。  
   Click `R` to reset the time.

4. PPT 全屏放映可自动倒计时。  
   Automatic countdown during full-screen PowerPoint presentation.

5. 点击时间可启动/暂停倒计时。  
   Click the time to start/pause the countdown.

6. 按 `Esc` 退出；在窗口空白处、时间或 `R` / `T` 上右键可选择「退出 Exit」。  
   Press `Esc` to exit, or right-click on an empty area, the time, or `R` / `T` to select "Exit".

7. 倒计时结束时窗口会闪烁提醒；是否自动退出 PPT 演示可在右键菜单中开关（默认关闭）。  
   The window flashes when countdown ends; auto-exit from PPT slideshow can be toggled in the right-click menu (off by default).

8. 点击 `T` 可切换主题（深色 / 浅色 / 蓝色 / 紫色），`R` 与 `T` 的背景色会跟随主题变化，主题偏好会自动保存。  
   Click `T` to switch themes (dark / light / blue / purple); `R` and `T` backgrounds follow the theme, and your preference is saved automatically.

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
git tag v1.1.0
git push origin v1.1.0
```

## 致谢 / Credits

Based on [sunnybluesea/PPT-Timer](https://github.com/sunnybluesea/PPT-Timer).
