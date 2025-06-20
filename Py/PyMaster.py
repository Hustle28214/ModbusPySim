
import modbus_tk.defines as cst
# from modbus_tk import modbus_rtu # 不使用RTU
import logging
import modbus_tk.hooks as modbusHooks
import modbus_tk.modbus_tcp as modbus_tcp   
import time
import modbus_tk
import sys

# 统一使用TCP/IP协议传输
def main():
    # 开一个日志
    errLogger = modbus_tk.utils.create_logger("console", level=logging.DEBUG)
    # 接收
    def recvHooks(data):
        master,bdata = data # 解包
        errLogger.info(bdata) # 要后面的字节数据
    # 全局钩子，捕获所有主站接收的原始字节
    modbusHooks.install_hook('modbus.Master.after_recv',recvHooks)
    try:
        def beforeConnect(args):
            master = args[0]
            errLogger.debug("master is {0} port is {1}".format(master._host,master._port))
        modbusHooks.install_hook("beforeConnect",beforeConnect)
        def recvData(args):
            bdata = args[1]
            errLogger.debug("receive data is {0} and the length is {1}".format(bdata,len(bdata)))
        modbusHooks.install_hook("recvData",recvData)
        serv = modbus_tcp.TcpMaster() # 默认是本机端口502，可以改：__init__()
        serv.get_timeout(2)
        errLogger.info("successful connect")
        # Init a modbus tcp server
        # serv.__init__("127.0.0.1",502) # 本机通讯
        # 解包，比如说读取保持寄存器
        errLogger.info(serv.execute(1,cst.READ_HOLDING_REGISTERS,3))# 从站地址1，起始地址=0, 读了三个寄存器
        # 写入浮点数
        serv.execute(1, cst.WRITE_MULTIPLE_REGISTERS, starting_address=0, output_value=[3.14], data_format='>f')
        # 读取浮点数
        errLogger.info(serv.execute(1, cst.READ_HOLDING_REGISTERS, 0, 2, data_format='>f'))
    except Exception as e:
        errLogger.error(sys.exc_info())

if __name__ == "__main__":
    main()