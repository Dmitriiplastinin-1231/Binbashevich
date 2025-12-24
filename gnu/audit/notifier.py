from flask import Flask, request, jsonify
from messenger import global_messenger

app = Flask(__name__)

@app.route('/')
def index():
    """Главная страница системы сообщений."""
    return """
    <html>
        <head>
            <title>Система сообщений</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
                h1 { color: #333; text-align: center; }
                .stats { background: #e3f2fd; padding: 10px; border-radius: 5px; margin: 10px 0; text-align: center; }
                .controls { text-align: center; margin: 20px 0; }
                button { background: #2196f3; color: white; border: none; padding: 10px 15px; margin: 0 5px; border-radius: 5px; cursor: pointer; }
                button:hover { background: #1976d2; }
                .message { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .message.unread { border-left: 4px solid #ff4444; background: #fff; }
                .message.read { border-left: 4px solid #ccc; background: #f9f9f9; }
                .message-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
                .message-type { font-weight: bold; color: #2c3e50; }
                .message-time { color: #7f8c8d; font-size: 12px; }
                .message-data { background: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; font-size: 12px; }
                .new-badge { background: #ff4444; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; margin-left: 10px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>💬 Сообщения системы</h1>
                
                <div class="stats" id="stats">Загрузка статистики...</div>
                
                <div class="controls">
                    <button onclick="loadMessages()">🔄 Обновить</button>
                    <button onclick="markAllAsRead()">✅ Прочитать все</button>
                </div>
                
                <div id="messages">Загрузка сообщений...</div>
            </div>

            <script>
                function loadMessages() {
                    fetch('/api/messages')
                        .then(r => r.json())
                        .then(data => {
                            displayMessages(data.messages);
                            updateStats(data.stats);
                        })
                        .catch(err => {
                            document.getElementById('messages').innerHTML = 'Ошибка: ' + err;
                        });
                }

                function displayMessages(messages) {
                    const container = document.getElementById('messages');
                    
                    if (messages.length === 0) {
                        container.innerHTML = '<div style="text-align: center; color: #666;">Нет сообщений</div>';
                        return;
                    }
                    
                    container.innerHTML = messages.map(msg => `
                        <div class="message ${msg.read ? 'read' : 'unread'}" onclick="markAsRead(${msg.id})">
                            <div class="message-header">
                                <div>
                                    <span class="message-type">${msg.type}</span>
                                    ${msg.read ? '' : '<span class="new-badge">НОВОЕ</span>'}
                                </div>
                                <div class="message-time">${new Date(msg.timestamp).toLocaleString()}</div>
                            </div>
                            <div class="message-data">${JSON.stringify(msg.data, null, 2)}</div>
                        </div>
                    `).join('');
                }

                function updateStats(stats) {
                    document.getElementById('stats').innerHTML = 
                        `📊 Сообщений: <strong>${stats.total_messages}</strong> | ` +
                        `Непрочитанных: <strong>${stats.unread_messages}</strong>`;
                }

                function markAsRead(messageId) {
                    fetch('/api/messages/mark_read', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({message_id: messageId})
                    }).then(() => loadMessages());
                }

                function markAllAsRead() {
                    fetch('/api/messages/mark_read', {
                        method: 'POST', 
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({all: true})
                    }).then(() => loadMessages());
                }

                // Автообновление каждые 2 секунды
                setInterval(loadMessages, 2000);

                // Первоначальная загрузка
                loadMessages();
            </script>
        </body>
    </html>
    """

@app.route('/api/messages')
def api_get_messages():
    """API для получения всех сообщений из ОБЩЕЙ системы."""
    try:
        messages = global_messenger.get_all_messages()
        stats = global_messenger.get_stats()
        
        print(f"🔍 API /api/messages: возвращаем {len(messages)} сообщений")
        
        return jsonify({
            'messages': messages,
            'stats': stats
        })
    except Exception as e:
        print(f"❌ Ошибка в /api/messages: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/mark_read', methods=['POST'])
def api_mark_as_read():
    """API для пометки сообщений как прочитанных в ОБЩЕЙ системе."""
    try:
        data = request.json
        message_id = data.get('message_id')
        
        if data.get('all'):
            global_messenger.mark_as_read()
        elif message_id:
            global_messenger.mark_as_read(message_id)
            
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Система сообщений запущена: http://127.0.0.1:8080/")
    print("💡 Все сообщения теперь хранятся в ОБЩЕМ файле!")
    app.run(debug=True, port=8080, host='127.0.0.1')