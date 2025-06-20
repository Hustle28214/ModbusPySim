from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
import socket

class LoggingDataBlock(ModbusSequentialDataBlock):
    """带分类日志的数据块"""
    def __init__(self, reg_type, *args, **kwargs):
        self.reg_type = reg_type  # 'AI'/'AO'/'DI'/'DO'
        super().__init__(*args, **kwargs)
    
    def getValues(self, address, count=1):
        values = super().getValues(address, count)
        print(f"{self.reg_type}读取 → 地址: {address}, 数量: {count}, 返回值: {values}")
        return values

    def setValues(self, address, values):
        print(f"{self.reg_type}写入 → 地址: {address}, 写入值: {values}")
        super().setValues(address, values)

def get_local_ip():
    """获取本机IP地址"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def run_slave():
    # 初始化带分类日志的寄存器
    store = ModbusSlaveContext(
        di=LoggingDataBlock('DI', 0, [0]*8),     # 离散输入
        co=LoggingDataBlock('DO', 0, [0]*8),     # 线圈
        hr=LoggingDataBlock('AO', 0, [0]*100),   # 保持寄存器(模拟输出)
        ir=LoggingDataBlock('AI', 0, [0]*100)    # 输入寄存器(模拟输入)
    )
    
    # 请求分类器
    def get_reg_type(function_code):
        return {
            1: 'DO', 2: 'DI', 3: 'AO', 4: 'AI',
            5: 'DO', 6: 'AO', 15: 'DO', 16: 'AO'
        }.get(function_code, 'UNKNOWN')
    
    class LoggingServerContext(ModbusServerContext):
        def __call__(self, request):
            reg_type = get_reg_type(request.function_code)
            print(f"\n=== {reg_type}操作请求 ===")
            print(f"功能码: {request.function_code}")
            print(f"从站ID: {request.unit_id}")
            if hasattr(request, 'address'):
                print(f"Modbus地址: {request.address} (实际地址: {request.address+1})")
            if hasattr(request, 'count'):
                print(f"读取数量: {request.count}")
            if hasattr(request, 'values'):
                print(f"写入数值: {request.values}")
            return super().__call__(request)

    context = LoggingServerContext(slaves=store, single=True)
    
    local_ip = get_local_ip()
    print(f"本机可用IP地址: {local_ip}")
    server_ip = input("请输入从站监听的IP地址（直接回车使用本机IP）: ") or local_ip
    port = 5020
    
    print("\nModbus从站配置信息:")
    print(f"IP: {server_ip}")
    print(f"端口: {port}")
    print("寄存器类型映射:")
    print("AI: 输入寄存器(模拟输入) | AO: 保持寄存器(模拟输出)")
    print("DI: 离散输入           | DO: 线圈(数字输出)")
    print("\n等待主站连接...")
    
    StartTcpServer(context, address=(server_ip, port))

if __name__ == "__main__":
    run_slave()