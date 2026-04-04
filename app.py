import os
import logging
from flask import Flask, request, jsonify

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8754058728:AAEc4420vw7LKJnScRKujASyt7lexQwYf8w"

flask_app = Flask(__name__)

@flask_app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """Простой вебхук для теста"""
    logger.info("=== Webhook получил запрос ===")
    logger.info(f"Headers: {dict(request.headers)}")
    
    try:
        data = request.get_json()
        logger.info(f"Data: {data}")
        
        # Просто отвечаем, что всё ок
        return jsonify({"ok": True}), 200
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"ok": False}), 500

@flask_app.route('/healthcheck')
def healthcheck():
    return "OK", 200

@flask_app.route('/')
def index():
    return "Test bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Запуск на порту {port}")
    flask_app.run(host='0.0.0.0', port=port)
