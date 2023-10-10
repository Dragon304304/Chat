# Sorry for the delay. No idea how to download msvcrt on replit but the code works when I run it through cmd.

import msvcrt
import select
import socket
import sys


def setup_sockets():
  global BOUND_SOCKET
  global PORT
  global USERNAME
  global BROADCASTER
  BOUND_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  BOUND_SOCKET.bind((IP, 0))
  BOUND_SOCKET.listen()
  PORT = BOUND_SOCKET.getsockname()[1]
  USERNAME = input("Please enter a username:\n")
  BROADCASTER = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                              socket.IPPROTO_UDP)
  request_chat_ports()


def request_chat_ports():
  BROADCASTER.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  BROADCASTER.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
  BROADCASTER.bind(('', 37020))
  BROADCASTER.sendto(f"^join|{PORT}|{USERNAME}|1|0".encode('ascii'),
                     ('<broadcast>', 37020))
  BROADCASTER.recv(1024).decode('ascii')


def run_chat():
  while True:
    manage_text_msg()
    rlist, wlist, xlist = select.select([BOUND_SOCKET] + RECV_USERS,
                                        SEND_USERS, [], 0)
    rlist += select.select([BROADCASTER], [], [], 0)[0]
    recv_messages(rlist)
    send_messages(wlist)


def manage_text_msg():
  global TEXT_MSG
  if not msvcrt.kbhit():
    return
  letter = msvcrt.getch().decode('ascii')
  if letter == '\r':
    if TEXT_MSG == "":
      return
    if TEXT_MSG.lower() == "/quit":
      terminate_self()
    print(f"{USERNAME} (You) -> {TEXT_MSG}")
    MESSAGES_TO_SEND.append((None, f"^msg|{TEXT_MSG}"))
    TEXT_MSG = ""
  elif letter == '\b':
    if len(TEXT_MSG) > 0:
      TEXT_MSG = TEXT_MSG[:-1]
  else:
    TEXT_MSG += letter


def recv_messages(rlist):
  for current_socket in rlist:
    if current_socket is BOUND_SOCKET:
      new_socket, address = BOUND_SOCKET.accept()
      RECV_USERS.append(new_socket)
    else:
      handle_message(current_socket)


def handle_message(user_socket):
  recv_data = user_socket.recv(1024).decode('ascii').split('|')
  if recv_data[0] == '':
    close_connection(user_socket)
  elif recv_data[0] == '^join':
    manage_new_user(user_socket, int(recv_data[1]), recv_data[2],
                    int(recv_data[3]), int(recv_data[4]))
  elif recv_data[0] == '^msg':
    print(f"{USERNAME_DICT[user_socket]} -> {recv_data[1]}")


def manage_new_user(og_socket, port, username, connect_to_socket,
                    save_new_user):
  if connect_to_socket:
    new_socket = open_connection(port)
    if save_new_user:
      MESSAGES_TO_SEND.append((new_socket, f"^join|{PORT}|{USERNAME}|0|1"))
    else:
      MESSAGES_TO_SEND.append((new_socket, f"^join|{PORT}|{USERNAME}|1|1"))
  if save_new_user:
    USERNAME_DICT[og_socket] = username
    print(f"{username} has joined the chat.")


def open_connection(port):
  new_socket = socket.socket()
  new_socket.connect(("127.0.0.1", port))
  SEND_USERS.append(new_socket)
  return new_socket


def close_connection(user_socket):
  if user_socket in RECV_USERS:
    RECV_USERS.remove(user_socket)
  if user_socket in SEND_USERS:
    SEND_USERS.remove(user_socket)
  print(f"{USERNAME_DICT[user_socket]} has left the chat.")
  user_socket.close()


def send_messages(wlist):
  for message in MESSAGES_TO_SEND:
    for current_socket in wlist:
      if current_socket == message[0] or message[0] is None:
        send_data = message[1].encode('ascii')
        current_socket.send(send_data)
        MESSAGES_TO_REMOVE.append(message)
  for message in MESSAGES_TO_REMOVE:
    if message in MESSAGES_TO_SEND:
      MESSAGES_TO_SEND.remove(message)


def terminate_self():
  BOUND_SOCKET.shutdown(socket.SHUT_RDWR)
  BOUND_SOCKET.close()
  sys.exit()


IP = '0.0.0.0'
PORT = 0
USERNAME = ""
global BOUND_SOCKET
global BROADCASTER
RECV_USERS = []
SEND_USERS = []
USERNAME_DICT = {}
MESSAGES_TO_SEND = []
MESSAGES_TO_REMOVE = []
TEXT_MSG = ""


def main():
  setup_sockets()
  run_chat()


if __name__ == "__main__":
  main()
