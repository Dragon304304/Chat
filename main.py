# not really sure if it properly runs on replit, but i'm pretty sure the code is fine
# for now the code is still made to work for multiple clients who don't know each other's ip

import select
import socket
import sys

RECV_SIZE = 1024


class ChatUser:

  def __init__(self):
    self.bound_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.bound_socket.bind(('0.0.0.0', 0))
    self.bound_socket.listen()
    self.broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                     socket.IPPROTO_UDP)
    self.username = input("Please enter a username:\n")
    self.username_dict = {}
    self.recv_users = []
    self.send_users = []
    self.messages_to_send = []
    self.text_msg = ""
    self.request_chat_ports()

  def request_chat_ports(self):
    self.broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    self.broadcaster.bind(('', 37020))
    self.broadcaster.sendto(
        f"^join|{socket.gethostbyname(socket.gethostname())}|{self.bound_socket.getsockname()[1]}|{self.username}|1|0"
        .encode('ascii'), ('<broadcast>', 37020))
    self.broadcaster.recv(RECV_SIZE).decode('ascii')

  def run_chat(self):
    while True:
      self.manage_text_msg()
      rlist, wlist, xlist = select.select(
          [self.bound_socket] + self.recv_users, self.send_users, [], 0)
      rlist += select.select([self.broadcaster], [], [], 0)[0]
      self.recv_messages(rlist)
      self.send_messages(wlist)

  def manage_text_msg(self):
    """if not msvcrt.kbhit():
      return
    letter = msvcrt.getch().decode('ascii')"""
    readable, _, _ = select.select([sys.stdin], [], [], 0.1)
    if not readable:
      return
    letter = sys.stdin.read(1)
    print(f"ch={letter}")
    if letter == '\r':
      if self.text_msg == "":
        return
      if self.text_msg.lower() == "/quit":
        self.terminate_self()
      print(f"{self.username} (You) -> {self.text_msg}")
      self.messages_to_send.append((None, f"^msg|{self.text_msg}"))
      self.text_msg = ""
    elif letter == '\b':
      if len(self.text_msg) > 0:
        self.text_msg = self.text_msg[:-1]
    else:
      self.text_msg += letter

  def recv_messages(self, rlist):
    for current_socket in rlist:
      if current_socket is self.bound_socket:
        new_socket, address = self.bound_socket.accept()
        self.recv_users.append(new_socket)
      else:
        self.handle_message(current_socket)

  def handle_message(self, user_socket):
    recv_data = user_socket.recv(RECV_SIZE).decode('ascii').split('|')
    if recv_data[0] == '':
      self.close_connection(user_socket)
    elif recv_data[0] == '^join':
      self.manage_new_user(user_socket, recv_data[1], int(recv_data[2]),
                           recv_data[3], int(recv_data[4]), int(recv_data[5]))
    elif recv_data[0] == '^msg':
      print(f"{self.username_dict[user_socket]} -> {recv_data[1]}")

  def manage_new_user(self, og_socket, ip, port, username, connect_to_socket,
                      save_new_user):
    if connect_to_socket:
      new_socket = self.open_connection(ip, port)
      if save_new_user:
        self.messages_to_send.append((
            new_socket,
            f"^join|{socket.gethostbyname(socket.gethostname())}|{self.bound_socket.getsockname()[1]}|{self.username}|0|1"
        ))
      else:
        self.messages_to_send.append((
            new_socket,
            f"^join|{socket.gethostbyname(socket.gethostname())}|{self.bound_socket.getsockname()[1]}|{self.username}|1|1"
        ))
    if save_new_user:
      self.username_dict[og_socket] = username
      print(f"{username} has joined the chat.")

  def open_connection(self, ip, port):
    new_socket = socket.socket()
    new_socket.connect((ip, port))
    self.send_users.append(new_socket)
    return new_socket

  def close_connection(self, user_socket):
    if user_socket in self.recv_users:
      self.recv_users.remove(user_socket)
    if user_socket in self.send_users:
      self.send_users.remove(user_socket)
    if user_socket in self.username_dict:
      print(f"{self.username_dict[user_socket]} has left the chat.")
    user_socket.close()

  def send_messages(self, wlist):
    messages_to_remove = []
    for message in self.messages_to_send:
      for current_socket in wlist:
        if current_socket == message[0] or message[0] is None:
          send_data = message[1].encode('ascii')
          current_socket.send(send_data)
          messages_to_remove.append(message)
    for message in messages_to_remove:
      if message in self.messages_to_send:
        self.messages_to_send.remove(message)

  def terminate_self(self):
    self.bound_socket.shutdown(socket.SHUT_RDWR)
    self.bound_socket.close()
    sys.exit()


def main():
  my_chat = ChatUser()
  my_chat.run_chat()


if __name__ == "__main__":
  main()
