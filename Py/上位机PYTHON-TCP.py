from pymodbus.client.sync import ModbusTcpClient as ModbusClient
import time
from datetime import datetime
import csv
import matplotlib.pyplot as plt
import warnings

# 忽略matplotlib的警告
warnings.filterwarnings("ignore")

class GreenhouseMonitor:
    def __init__(self, ip_address='192.168.108.238', port=502):
        self.client = ModbusClient(ip_address, port)
        self.temp_data = []
        self.humid_data = []
        self.time_data = []
        self.max_temp = 30.0  # 温度上限(℃)
        self.min_temp = 15.0   # 温度下限(℃)
        self.max_humid = 80.0  # 湿度上限(%)
        self.min_humid = 40.0  # 湿度下限(%)
        
    def read_sensor_data(self):
        try:
            # 连接Modbus服务器
            if not self.client.connect():
                print("无法连接到Modbus服务器")
                return None, None
            
            # 读取保持寄存器(地址0和1)
            temp_reg = self.client.read_holding_registers(0, 1, unit=1)
            humid_reg = self.client.read_holding_registers(1, 1, unit=1)
            
            if temp_reg.isError() or humid_reg.isError():
                print("读取寄存器错误")
                return None, None
                
            # 将寄存器值转换回浮点数(之前放大了100倍)
            temperature = temp_reg.registers[0] / 100.0
            humidity = humid_reg.registers[0] / 100.0
            
            return temperature, humidity
            
        except Exception as e:
            print(f"发生错误: {e}")
            return None, None
        finally:
            self.client.close()
    
    def check_thresholds(self, temp, humid):
        alerts = []
        if temp > self.max_temp:
            alerts.append(f"高温警告: {temp}°C > {self.max_temp}°C")
        if temp < self.min_temp:
            alerts.append(f"低温警告: {temp}°C < {self.min_temp}°C")
        if humid > self.max_humid:
            alerts.append(f"高湿警告: {humid}% > {self.max_humid}%")
        if humid < self.min_humid:
            alerts.append(f"低湿警告: {humid}% < {self.min_humid}%")
        return alerts
    
    def log_data(self, temp, humid):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_data.append(timestamp)
        self.temp_data.append(temp)
        self.humid_data.append(humid)
        
        # 写入CSV文件
        with open('greenhouse_data.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, temp, humid])
    
    def plot_data(self):
        if len(self.time_data) < 2:
            print("数据不足，无法生成图表")
            return
            
        # 将时间字符串转换为datetime对象
        times = [datetime.strptime(t, "%Y-%m-%d %H:%M:%S") for t in self.time_data]
        
        plt.figure(figsize=(12, 6))
        
        # 绘制温度曲线
        plt.subplot(2, 1, 1)
        plt.plot(times, self.temp_data, 'r-', label='Temperature (°C)')
        plt.axhline(y=self.max_temp, color='r', linestyle='--', label='Max Temp')
        plt.axhline(y=self.min_temp, color='b', linestyle='--', label='Min Temp')
        plt.ylabel('Temperature (°C)')
        plt.title('Greenhouse Environment Monitoring')
        plt.legend()
        plt.grid()
        
        # 绘制湿度曲线
        plt.subplot(2, 1, 2)
        plt.plot(times, self.humid_data, 'b-', label='Humidity (%)')
        plt.axhline(y=self.max_humid, color='r', linestyle='--', label='Max Humid')
        plt.axhline(y=self.min_humid, color='b', linestyle='--', label='Min Humid')
        plt.ylabel('Humidity (%)')
        plt.legend()
        plt.grid()
        
        plt.tight_layout()
        plt.show()
    
    def monitor(self, interval=5):
        try:
            while True:
                temp, humid = self.read_sensor_data()
                if temp is not None and humid is not None:
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - "
                          f"Temperature: {temp:.2f}°C, Humidity: {humid:.2f}%")
                    
                    # 检查阈值
                    alerts = self.check_thresholds(temp, humid)
                    for alert in alerts:
                        print(f"! ALERT: {alert}")
                    
                    # 记录数据
                    self.log_data(temp, humid)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n监测停止")
            self.plot_data()

if __name__ == "__main__":
    # 创建监控实例(替换为你的ESP32 IP地址)
    monitor = GreenhouseMonitor(ip_address='192.168.108.238')
    
    # 开始监测(每5秒读取一次)
    monitor.monitor(interval=5)