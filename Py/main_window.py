import sys
import socket
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QTextEdit, QLineEdit, 
                            QPushButton, QGroupBox, QMessageBox)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject, QThread
from PyQt5 import QtGui
from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock

class ModbusServerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.server_worker = None
        self.worker_thread = None
        self.setup_ui()
        self.setWindowTitle("Modbus从站监控器")
        self.resize(900, 650)
        self.setup_styles()
        self.get_local_ip()

    def setup_ui(self):
        # 主控件
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        
        # 左侧配置面板
        left_panel = QVBoxLayout()
        
        # 网络配置组
        net_group = QGroupBox("网络配置")
        net_layout = QVBoxLayout()
        
        self.ip_label = QLabel("监听IP地址:")
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("例如: 192.168.1.100")
        
        self.get_ip_btn = QPushButton("获取本机IP")
        self.get_ip_btn.clicked.connect(self.get_local_ip)
        
        self.port_label = QLabel("端口号:")
        self.port_input = QLineEdit("5020")
        self.port_input.setValidator(QtGui.QIntValidator(1, 65535))
        
        net_layout.addWidget(self.ip_label)
        net_layout.addWidget(self.ip_input)
        net_layout.addWidget(self.get_ip_btn)
        net_layout.addWidget(self.port_label)
        net_layout.addWidget(self.port_input)
        net_group.setLayout(net_layout)
        
        # 服务器控制组
        ctrl_group = QGroupBox("服务器控制")
        ctrl_layout = QVBoxLayout()
        
        self.start_btn = QPushButton("启动服务器")
        self.start_btn.clicked.connect(self.toggle_server)
        
        self.status_label = QLabel("状态: 未运行")
        
        ctrl_layout.addWidget(self.start_btn)
        ctrl_layout.addWidget(self.status_label)
        ctrl_layout.addStretch()
        ctrl_group.setLayout(ctrl_layout)
        
        # 寄存器映射说明
        desc_group = QGroupBox("寄存器映射说明")
        desc_layout = QVBoxLayout()
        desc_text = QLabel("""
        <b>地址映射表:</b>
        <table>
        <tr><td>AI</td><td>输入寄存器</td><td>30001-30100</td></tr>
        <tr><td>AO</td><td>保持寄存器</td><td>40001-40100</td></tr>
        <tr><td>DI</td><td>离散输入</td><td>10001-10008</td></tr>
        <tr><td>DO</td><td>线圈</td><td>00001-00008</td></tr>
        </table>
        <p>注: LabVIEW地址 = Python地址 + 1</p>
        """)
        desc_text.setTextFormat(Qt.RichText)
        desc_layout.addWidget(desc_text)
        desc_group.setLayout(desc_layout)
        
        left_panel.addWidget(net_group)
        left_panel.addWidget(ctrl_group)
        left_panel.addWidget(desc_group)
        
        # 右侧监控面板
        right_panel = QVBoxLayout()
        
        # 通信日志组
        log_group = QGroupBox("通信日志 (实时更新)")
        log_layout = QVBoxLayout()
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QtGui.QFont("Consolas", 10))
        
        log_tools = QHBoxLayout()
        self.clear_btn = QPushButton("清空日志")
        self.clear_btn.clicked.connect(self.clear_logs)
        self.pause_btn = QPushButton("暂停刷新")
        self.pause_btn.setCheckable(True)
        
        log_tools.addWidget(self.clear_btn)
        log_tools.addWidget(self.pause_btn)
        log_tools.addStretch()
        
        log_layout.addWidget(self.log_display)
        log_layout.addLayout(log_tools)
        log_group.setLayout(log_layout)
        
        # 寄存器状态组
        status_group = QGroupBox("寄存器状态监控")
        status_layout = QVBoxLayout()
        
        self.register_status = QTextEdit()
        self.register_status.setReadOnly(True)
        self.register_status.setFont(QtGui.QFont("Consolas", 9))
        
        status_layout.addWidget(self.register_status)
        status_group.setLayout(status_layout)
        
        right_panel.addWidget(log_group, 70)
        right_panel.addWidget(status_group, 30)
        
        # 组合主布局
        main_layout.addLayout(left_panel, 30)
        main_layout.addLayout(right_panel, 70)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # 状态更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_register_status)
        self.update_timer.start(1000)

    def setup_styles(self):
        self.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                border: 1px solid gray; 
                border-radius: 5px;
                margin-top: 10px;
            }
            QTextEdit { 
                font-family: Consolas, Courier New; 
                font-size: 11pt; 
            }
            QPushButton#start_btn {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton#stop_btn {
                background-color: #f44336;
                color: white;
                font-weight: bold;
            }
        """)
        self.start_btn.setObjectName("start_btn")

    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            self.ip_input.setText(ip)
            self.log_message(f"自动获取到本机IP: {ip}")
        except Exception as e:
            self.show_error(f"获取IP失败: {str(e)}")
        finally:
            s.close()

    def log_message(self, message):
        """在日志框中显示消息"""
        if not self.pause_btn.isChecked():
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.log_display.append(f"[{timestamp}] {message}")
            scrollbar = self.log_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def clear_logs(self):
        """清空日志"""
        self.log_display.clear()

    def show_error(self, message):
        """显示错误弹窗"""
        QMessageBox.critical(self, "错误", message)

    def validate_ip(self, ip):
        """验证IP地址格式"""
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    def toggle_server(self):
        """启动/停止服务器"""
        if self.server_worker and self.worker_thread.isRunning():
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        """启动Modbus服务器线程"""
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()
        
        # 输入验证
        if not ip:
            self.show_error("请输入IP地址")
            return
        if not self.validate_ip(ip):
            self.show_error("无效的IP地址格式")
            return
        if not port.isdigit():
            self.show_error("端口号必须为数字")
            return
        
        port = int(port)
        
        try:
            # 检查端口是否可用
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.bind((ip, port))
            test_socket.close()
        except OSError as e:
            self.show_error(f"无法绑定到{ip}:{port}\n错误: {str(e)}")
            return
        
        self.log_message(f"正在启动Modbus从站 @ {ip}:{port}...")
        
        # 初始化数据存储
        store = ModbusSlaveContext(
            di=LoggingDataBlock('DI', 0, [0]*8, self.log_message),
            co=LoggingDataBlock('DO', 0, [0]*8, self.log_message),
            hr=LoggingDataBlock('AO', 0, [0]*100, self.log_message),
            ir=LoggingDataBlock('AI', 0, [0]*100, self.log_message)
        )
        
        # 创建线程和工作对象
        self.worker_thread = QThread()
        self.server_worker = ServerWorker(ip, port, store)
        self.server_worker.moveToThread(self.worker_thread)
        
        # 连接信号槽
        self.worker_thread.started.connect(self.server_worker.run)
        self.server_worker.finished.connect(self.worker_thread.quit)
        self.server_worker.finished.connect(self.server_worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.server_worker.log_signal.connect(self.log_message)
        
        # 启动线程
        self.worker_thread.start()
        
        # 更新UI状态
        self.start_btn.setText("停止服务器")
        self.start_btn.setObjectName("stop_btn")
        self.start_btn.style().polish(self.start_btn)
        self.status_label.setText(f"状态: 运行中 ({ip}:{port})")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.ip_input.setEnabled(False)
        self.port_input.setEnabled(False)
        self.get_ip_btn.setEnabled(False)

    def stop_server(self):
        """停止服务器"""
        if self.server_worker:
            self.server_worker.stop()
            if self.worker_thread:
                self.worker_thread.quit()
                self.worker_thread.wait()
            
            self.log_message("服务器已停止")
            
            # 恢复UI状态
            self.start_btn.setText("启动服务器")
            self.start_btn.setObjectName("start_btn")
            self.start_btn.style().polish(self.start_btn)
            self.status_label.setText("状态: 已停止")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.ip_input.setEnabled(True)
            self.port_input.setEnabled(True)
            self.get_ip_btn.setEnabled(True)

    def update_register_status(self):
        """更新寄存器状态显示"""
        if not hasattr(self, 'server_worker') or not self.server_worker or self.pause_btn.isChecked():
            return
            
        try:
            store = self.server_worker.store
            status_text = []
            
            # 显示DO线圈状态 (地址0-7)
            do_values = store.getValues(0x01, 0, 8)  # 0x01 = 读线圈
            status_text.append("=== DO线圈状态 (地址0-7) ===")
            status_text.append(" ".join(f"{i}:{'●' if v else '○'}" for i, v in enumerate(do_values)))
            
            # 显示DI离散输入 (地址0-7)
            di_values = store.getValues(0x02, 0, 8)  # 0x02 = 读离散输入
            status_text.append("\n=== DI离散输入 (地址0-7) ===")
            status_text.append(" ".join(f"{i}:{'●' if v else '○'}" for i, v in enumerate(di_values)))
            
            # 显示AO保持寄存器 (地址0-9)
            ao_values = store.getValues(0x03, 0, 10)  # 0x03 = 读保持寄存器
            status_text.append("\n=== AO保持寄存器 (地址0-9) ===")
            status_text.append("\n".join(f"地址{i}: {v:5}" for i, v in enumerate(ao_values)))
            
            # 显示AI输入寄存器 (地址0-9)
            ai_values = store.getValues(0x04, 0, 10)  # 0x04 = 读输入寄存器
            status_text.append("\n=== AI输入寄存器 (地址0-9) ===")
            status_text.append("\n".join(f"地址{i}: {v:5}" for i, v in enumerate(ai_values)))
            
            self.register_status.setPlainText("\n".join(status_text))
        except Exception as e:
            self.log_message(f"更新寄存器状态错误: {str(e)}")

    def closeEvent(self, event):
        """窗口关闭时停止服务器"""
        self.stop_server()
        event.accept()

class ServerWorker(QObject):
    """Modbus服务器工作对象"""
    log_signal = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, ip, port, store):
        super().__init__()
        self.ip = ip
        self.port = port
        self.store = store
        self._running = True
        
    def run(self):
        context = ModbusServerContext(slaves=self.store, single=True)
        self.log_signal.emit(f"Modbus从站已启动: {self.ip}:{self.port}")
        
        try:
            self.server = StartTcpServer(
                context=context,
                address=(self.ip, self.port),
                defer_reactor_run=True
            )
            while self._running:
                QThread.msleep(100)
        except Exception as e:
            self.log_signal.emit(f"服务器错误: {str(e)}")
        finally:
            if hasattr(self, 'server'):
                self.server.server_close()
            self.finished.emit()
    
    def stop(self):
        self._running = False

class LoggingDataBlock(ModbusSequentialDataBlock):
    """带日志记录的数据块"""
    def __init__(self, reg_type, address, values, log_callback):
        super().__init__(address, values)
        self.reg_type = reg_type
        self.log_callback = log_callback
    
    def getValues(self, address, count=1):
        values = super().getValues(address, count)
        self.log_callback(
            f"{self.reg_type}读取 → 地址: {address}, 数量: {count}, 返回值: {values}"
        )
        return values

    def setValues(self, address, values):
        self.log_callback(
            f"{self.reg_type}写入 → 地址: {address}, 写入值: {values}"
        )
        super().setValues(address, values)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModbusServerGUI()
    window.show()
    sys.exit(app.exec_())