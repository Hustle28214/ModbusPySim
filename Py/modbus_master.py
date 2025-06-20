# modbus_master.py
from pymodbus.client import ModbusTcpClient
from PyQt5.QtCore import QObject, pyqtSignal

class ModbusMaster(QObject):
    data_updated = pyqtSignal(dict)
    
    def __init__(self, ip='127.0.0.1', port=5020):
        super().__init__()
        self.client = ModbusTcpClient(ip, port=port)
        self.registers = {
            'speed': 0,
            'start': False,
            'sensors': [0]*8
        }
        
    def connect(self):
        return self.client.connect()
        
    def read_data(self):
        """读取所有需要的数据"""
        try:
            # 读取保持寄存器(地址0:速度, 地址1:启动状态)
            hr_result = self.client.read_holding_registers(0, 2)
            # 读取离散输入(传感器状态)
            di_result = self.client.read_discrete_inputs(0, 8)
            
            if not hr_result.isError() and not di_result.isError():
                self.registers.update({
                    'speed': hr_result.registers[0],
                    'start': bool(hr_result.registers[1]),
                    'sensors': [int(b) for b in di_result.bits]
                })
                self.data_updated.emit(self.registers)
                return True
        except Exception as e:
            print(f"读取错误: {e}")
        return False
        
    def write_register(self, address, value):
        """写入单个寄存器"""
        try:
            result = self.client.write_register(address, value)
            return not result.isError()
        except Exception as e:
            print(f"写入错误: {e}")
            return False
            
    def close(self):
        self.client.close()