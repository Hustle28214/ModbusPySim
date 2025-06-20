# web_monitor.py
from flask import Flask, render_template_string
from threading import Lock
import json

app = Flask(__name__)
data = {"speed": 0, "start": False, "sensors": [0]*8}
data_lock = Lock()

@app.route('/')
def dashboard():
    with data_lock:
        return render_template_string('''
        <h1>Modbus监控</h1>
        <p>速度: {{ speed }}%</p>
        <p>状态: {{ "运行" if start else "停止" }}</p>
        <h3>传感器状态:</h3>
        {% for s in sensors %}
        <div>Sensor {{ loop.index0 }}: {{ "触发" if s else "正常" }}</div>
        {% endfor %}
        ''', **data)

@app.route('/api/data')
def get_data():
    with data_lock:
        return json.dumps(data)

if __name__ == '__main__':
    app.run(port=5000)