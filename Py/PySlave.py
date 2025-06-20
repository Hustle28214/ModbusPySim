import modbus_tk.defines as cst
# from modbus_tk import modbus_rtu # 不使用RTU
import logging
import modbus_tk.modbus_tcp as modbus_tcp   
import time
import modbus_tk
import sys

def main():
    # 开一个日志
    errLogger = modbus_tk.utils.create_logger("console", level=logging.DEBUG)
    try:
        # 初始化一个从机
        slave = modbus_tcp.TcpServer() # 默认本机地址，端口502
        errLogger.info("slave start")
        slave.start()

        # 添加从站1
        slave_1 = slave.add_slave(1) # 1就是从站号
        slave_1.add_block('0',cst.HOLDING_REGISTERS,0,10) # 0是块号，寄存器类型，起始地址，寄存器数量

        while True:
            time.sleep(1)
            cmd = sys.stdin.readline()
            args = cmd.split(' ')

            if cmd.find('quit') == 0:
                sys.stdout.write('quit\r\n')
                break
            elif args[0] =='add_slave':
                # 接收到添加从站的指令
                slave_id = int(args[1])
                slave.add_slave(slave_id)
                sys.stdout.write('add slave {0}\r\n'.format(slave_id))
            elif args[0] == 'add_block':
                # 接收到添加块的指令
                slave_id = int(args[1])
                name = args[2]
                block_type = args[3]
                start_addr = int(args[4])
                quantity = int(args[5])
                slaveAddBlock = slave.get_slave(slave_id)
                slaveAddBlock.add_block(name,block_type,start_addr,quantity)
                sys.stdout.write('add block {0} to slave {1}\r\n'.format(name,slave_id))
            elif args[0] == 'set_values':
                # 接收到设置值的指令
                slave_id = int(args[1])
                name = args[2]
                values = [int(x) for x in args[3:]]
                slaveSetValues = slave.get_slave(slave_id)
                slaveSetValues.set_values(name,values)
                sys.stdout.write('set values {0} to slave {1}\r\n'.format(values,slave_id))
            elif args[0] == 'get_values':
                # 接收到获取值的指令
                slave_id = int(args[1])
                name = args[2]
                start_addr = int(args[3])
                quantity = int(args[4])
                slaveGetValues = slave.get_slave(slave_id)
                values = slaveGetValues.get_values(name,start_addr,quantity)
                sys.stdout.write('get values {0} from slave {1}\r\n'.format(values,slave_id))
            else:
                sys.stdout.write('unknown command\r\n')
    finally:
        # 关闭从站
        slave.stop()

if __name__ == "__main__":
    main()