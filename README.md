# LINE 打卡系統

一個使用 LINE Login、LIFF 和 Messaging API 實現的簡單打卡系統。

## 功能

- 使用 LINE 帳號登入
- 位置打卡
- 自動將打卡記錄發送到 LINE 群組
- 防止重複打卡

## 設置步驟

1. 在 LINE Developers 創建 LINE Login 頻道
2. 在 LINE Login 頻道中添加 LIFF 應用
3. 創建 Messaging API 頻道
4. 設置環境變數
5. 部署應用

## 環境變數

- LINE_LOGIN_CHANNEL_ID: LINE Login 頻道 ID
- LINE_LOGIN_CHANNEL_SECRET: LINE Login 頻道密鑰
- LIFF_ID: LIFF 應用 ID
- MESSAGING_CHANNEL_ACCESS_TOKEN: Messaging API 頻道訪問權杖
- LINE_GROUP_ID: LINE 群組 ID

## 安裝與執行

```bash
# 安裝依賴
pip install -r requirements.txt

# 運行應用
python app.py
