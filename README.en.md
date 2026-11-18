# PPTimer

[中文](README.md)丨English

A free-for-life PowerPoint countdown timer.

## Download and install

Download build outputs from [GitHub Releases](https://github.com/scsagentclub/PPTimer/releases):

- `PPTimer.zip`: portable edition. Extract the ZIP and run `PPTimer.exe`.
- `PPTimer-1.2.0-win64.msi`: Windows 64-bit installer. Installs for the current user, creates a Start menu shortcut, and supports uninstalling from Windows Settings.

## Usage

1. No installation required; simply place on your desktop and click to run. The default countdown is 7 minutes.
2. Use `+` / `-` or the scroll wheel to adjust by one minute. While paused, press `S` or use the context menu to enter minutes or `mm:ss` (up to 99:59).
3. Click `R` or press `R` to reset, preserving custom seconds.
4. The countdown starts automatically during full-screen PowerPoint presentations.
5. Click the time to start or pause the countdown.
6. Press `Esc` to exit, or right-click on an empty area, the time, or `R` / `T` to select "Exit".
7. When the timer ends, the window flashes, exits the current full-screen presentation by default, and stays at `00:00`. There is no break mode. Press `R` to restore the configured duration, or click the time to start another countdown. Auto-exit can be disabled in the context menu; the setting is saved, and existing saved preferences are preserved.
8. Click `T` to choose from six themes: Dark, Light, Blue, Purple, Warm Orange, and Mint. Blue is the default, and your theme preference is saved automatically. Use the context menu to toggle always-on-top.

The app targets Windows and uses Windows APIs for full-screen detection. The source entry point is `PPT-Timer.py`. Full-screen detection uses the presentation window's own monitor and is not limited to PowerPoint. The timer tracks the presentation window so it can exit that presentation when time expires even after you click the timer.

## Build

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

## GitHub Actions automated builds

Push a `v*` tag matching `VERSION` to trigger an automated build. For example, when `VERSION` is `1.2.0`:

```bash
git tag v1.2.0
git push origin v1.2.0
```

The workflow builds the ZIP and MSI, verifies MSI installation and uninstallation, and uploads both outputs to the corresponding GitHub Release. You can also run the workflow manually from the Actions page and download its build artifacts.

To add an MSI to the existing v1.2.0 release, select **Build Windows ZIP and MSI** in Actions, click **Run workflow**, select the `main` branch, and set `release_tag` to `v1.2.0`. The workflow downloads the existing release ZIP, packages its EXE as an MSI, and attaches the installer to that release.

## Credits

Based on [sunnybluesea/PPT-Timer](https://github.com/sunnybluesea/PPT-Timer).
