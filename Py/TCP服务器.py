import socket
import threading

# 标志变量 用于停止服务器
is_running = True

def handle_client_connection(client_socket):
    try:
        # 接收客户端发送的路径数据（接收TCP客户端的信息）
        file_path = client_socket.recv(1024).decode()
        print(f"接收到的文件路径: {file_path}")

        # 返回接收到的文件路径（发送信息给TCP客户端）
        client_socket.sendall(file_path.encode())
    finally:
        client_socket.close()

def tcp_server():
    global is_running
    # 创建一个 TCP 套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 将套接字绑定到所有可用的网络接口和指定端口
    server_socket.bind(('0.0.0.0', 12345))
    # 监听传入连接的最大数量
    server_socket.listen(5)
    # 设置套接字超时时间为1秒
    server_socket.settimeout(1)
    print("服务器正在监听端口 12345")

    # 创建一个线程来等待停止命令
    def stop_server():
        global is_running
        input("按Enter键停止服务器...\n")
        is_running = False

    # 启动停止服务器的线程
    stop_thread = threading.Thread(target=stop_server)
    stop_thread.start()

    # 等待客户端连接
    while is_running:
        try:
            # 接受客户端连接，返回连接套接字和客户端地址
            client_socket, addr = server_socket.accept()
            print(f"与 {addr} 建立连接")
            # 创建一个新的线程来处理客户端连接
            client_handler = threading.Thread(
                target=handle_client_connection,
                args=(client_socket,)
            )
            client_handler.start()
        except socket.timeout:
            # 如果发生超时，则继续等待连接
            continue
        except Exception as e:
            # 捕获其他异常并打印错误消息
            print(f"服务器错误: {e}")
            break

    # 关闭服务器套接字
    server_socket.close()
    print("服务器已关闭")

if __name__ == "__main__":
    tcp_server()