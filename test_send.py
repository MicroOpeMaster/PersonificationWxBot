"""
简单测试脚本 - 发送消息到文件传输助手
运行方式: python test_send.py
"""
import pyautogui
import pyperclip
import time

print("准备发送消息到文件传输助手...")
print("请确保微信已打开")

# 激活微信
print("1. 激活微信窗口")
pyautogui.hotkey('ctrl', 'alt', 'w')
time.sleep(1)

# 搜索联系人
print("2. 搜索文件传输助手")
pyautogui.hotkey('ctrl', 'f')
time.sleep(0.5)
pyperclip.copy('文件传输助手')
pyautogui.hotkey('ctrl', 'v')
time.sleep(0.5)
pyautogui.press('enter')
time.sleep(0.5)
pyautogui.press('esc')
time.sleep(0.3)

# 发送消息
print("3. 发送测试消息")
pyperclip.copy('你好，这是微信机器人测试消息！')
pyautogui.hotkey('ctrl', 'v')
time.sleep(0.2)
pyautogui.press('enter')

print("\n消息已发送！请检查微信文件传输助手")