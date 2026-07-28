# Android Appium (Phase H)

## Scope
Phone/tablet *local app control* is intentionally stubbed. Telegram remains the remote command channel; the Windows connector is the executor.

## Enable later
1. Install Appium Server and UiAutomator2.
2. Connect Android device/emulator (`adb devices`).
3. Set env:
   - `APPIUM_SERVER_URL=http://127.0.0.1:4723`
   - `ANDROID_CAPABILITIES={"platformName":"Android","automationName":"UiAutomator2","deviceName":"..."}`
4. Replace `connector/mobile/appium_stub.py` with a real WebDriver session.
5. Register device id `android-phone` in the task queue.

## Current behavior
`open ... on my android tablet` does **not** execute on device.
