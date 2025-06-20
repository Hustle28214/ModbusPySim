# test_modbus_system.py
import unittest
from pymodbus.client import ModbusTcpClient
from threading import Thread
from modbus_slave_simulator import run_slave

class TestModbusSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 启动模拟从站
        cls.slave_thread = Thread(target=run_slave, daemon=True)
        cls.slave_thread.start()
        
        # 创建测试客户端
        cls.client = ModbusTcpClient('localhost', port=5020)
        cls.client.connect()
        
    def test_speed_control(self):
        # 测试速度控制
        test_values = [0, 50, 100]
        for val in test_values:
            self.client.write_register(0, val)
            result = self.client.read_holding_registers(0, 1)
            self.assertEqual(result.registers[0], val)
            
    def test_start_stop(self):
        # 测试启停控制
        self.client.write_register(1, 1)
        result = self.client.read_holding_registers(1, 1)
        self.assertEqual(result.registers[0], 1)
        
        self.client.write_register(1, 0)
        result = self.client.read_holding_registers(1, 1)
        self.assertEqual(result.registers[0], 0)
        
    @classmethod
    def tearDownClass(cls):
        cls.client.close()

if __name__ == '__main__':
    unittest.main()