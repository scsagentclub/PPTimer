# PPTimer

A lifetime-free PowerPoint countdown timer software.

## 使用说明 / Usage

1. 软件不用安装，放置桌面点击即可运行。  
   No installation required; simply place on your desktop and click to run.

2. `+` / `-` 或滚轮可调整时间。  
   Use the `+/-` keys or scroll wheel to adjust the time.

3. 点击 logo 可重置时间。  
   Click the logo to reset the time.

4. PPT 全屏放映可自动倒计时。  
   Automatic countdown during full-screen PowerPoint presentation.

5. 点击时间可启动/暂停倒计时。  
   Click the time to start/pause the countdown.

6. 按 `Esc` 退出；在窗口空白处或 logo 上右键可选择「退出 Exit」。  
   Press `Esc` to exit, or right-click on an empty area or the logo to select "Exit".

7. 点击 `T` 按钮可切换主题（深色 / 浅色 / 蓝色 / 紫色），主题偏好会自动保存。  
   Click the `T` button to switch themes (dark / light / blue / purple); your preference is saved automatically.

## 自行打包 / Build

### Windows 本地打包

```bash
pip install -r requirements.txt
python build.py          # 生成 PPTimer.zip（便携版）
python setup.py bdist_msi # 生成 MSI 安装包
```

### GitHub Actions 自动构建

推送到 `v*` tag 即可触发自动构建，产物包含 `PPTimer.zip` 和 `PPTimer.msi`：

```bash
git tag v1.1.0
git push origin v1.1.0
```

## 致谢 / Credits

Based on [sunnybluesea/PPT-Timer](https://github.com/sunnybluesea/PPT-Timer).
