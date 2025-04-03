# LINE 打卡系統

一個使用 LINE Login、LIFF 和 Messaging API 實現的簡單打卡系統，支持多種功能的員工簽到與學習平台。

## 功能

- 使用 LINE 帳號登入
- 位置打卡（上班/下班）
- 自動將打卡記錄發送到 LINE 群組
- 防止重複打卡
- 每日單字學習功能
- 數據導出（Excel、PDF、Google Sheets）
- 上下班提醒設置
- 週報、月報自動生成

## 系統架構

- 模型層 (Model): 提供數據存取和基本業務邏輯
- 服務層 (Service): 處理複雜業務邏輯
- 路由層 (Route): 處理 HTTP 請求和 LINE 訊息

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
- TIMEZONE: 系統時區，預設 'Asia/Taipei'

## 安裝與執行

```bash
# 安裝依賴
pip install -r requirements.txt

# 運行應用
python app.py

```

## 指令清單

- !今日單字學習 - 獲取今日學習單字
- !設置上班提醒 HH:MM - 設置上班提醒時間
- !設置下班提醒 HH:MM - 設置下班提醒時間
- !系統狀態 - 查看系統運行狀態

## 最近更新

- 重構數據模型層，採用類結構提高代碼可維護性
- 添加詞彙學習功能，支持用戶專屬詞彙分配
- 增強錯誤處理，確保系統穩定性
- 優化提醒功能，支持自定義提醒時間
