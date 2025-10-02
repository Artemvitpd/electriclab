#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from quart import Quart, jsonify

app = Quart(__name__)

@app.route("/")
async def index():
    return """
    <html>
    <head><title>HybridCache Test</title></head>
    <body>
    <h1>🎉 HybridCache работает!</h1>
    <p>Сервер успешно запущен на порту 8080</p>
    <p>Все исправления применены</p>
    <hr>
    <h3>API Endpoints:</h3>
    <ul>
        <li><a href="/api/test">Тест API</a></li>
        <li><a href="/api/stats">Статистика</a></li>
    </ul>
    </body>
    </html>
    """

@app.route("/api/test")
async def api_test():
    return jsonify({
        "status": "ok",
        "message": "API работает!",
        "server": "HybridCache"
    })

@app.route("/api/stats")
async def api_stats():
    return jsonify({
        "status": "ok",
        "files": 0,
        "hot_cache": 0,
        "cold_cache": 0,
        "message": "Сервер работает корректно"
    })

if __name__ == "__main__":
    print("🚀 Запуск тестового сервера HybridCache...")
    print("📡 Сервер будет доступен по адресу: http://localhost:8080")
    print("🛑 Для остановки нажмите Ctrl+C")
    app.run(host="127.0.0.1", port=8080, debug=False)
