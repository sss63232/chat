#!/usr/bin/osascript

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title 啟動開發佈局
# @raycast.mode silent
# @raycast.icon 💻

-- 取得螢幕尺寸
tell application "Finder"
	set screenResolution to bounds of window of desktop
	set screenWidth to item 3 of screenResolution
	set screenHeight to item 4 of screenResolution
end tell

-- 左半邊：Safari (Chrome 支援直接設定 bounds)
if application "Safari" is running then
	tell application "Safari"
		activate
		set bounds of window 1 to {0, 25, screenWidth / 2, screenHeight}
	end tell
end if

-- 右半邊：Claude (改透過 macOS 系統事件強制設定)
if application "Claude" is running then
	tell application "Claude" to activate
	delay 0.2 -- 稍微等待 0.2 秒，確保 Claude 視窗已切換到最上層
	
	tell application "System Events"
		-- Claude 在系統背後的程序名稱叫做 "Code"
		if exists (process "Code") then
			tell process "Code"
				-- 設定視窗左上角的座標 (X, Y)
				set position of window 1 to {screenWidth / 2, 25}
				-- 設定視窗的寬度與高度
				set size of window 1 to {screenWidth / 2, screenHeight - 25}
			end tell
		end if
	end tell
end if