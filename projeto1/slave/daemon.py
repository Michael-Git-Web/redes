#!/usr/bin/env python3
import argparse
import socket
import threading
import logging
import subprocess
import sys

import protocol
import util


config = util.get_config()

class Command():
	def validate(cmd):
		'''
		A daemon deve fazer a checagem prévia destas opções antes de
		executá-las, garantido que parâmetros maliciosos como 
		"|", ";" e ">" não sejam executados
		'''
		import re
		logging.debug("re")
		if re.search(r"[|;>]", cmd) is not None:
			logging.debug("re failed")
			return False
		logging.debug("re suc")
		
		return True


	def execute(cmd):
		# Shell True é necessário considerando que cmd é uma string unica
		# e não uma lista de parametros
		try:
			logging.debug("subprocess.run(%s)" % cmd)
			process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		except:
			e = sys.exc_info()[0]
			stdout = 'failed to execute process %s' % e
		else:
			if len(process.stdout):
				stdout = process.stdout.decode()
			else:
				stdout = process.stderr.decode()
		return stdout


	def try_to_execute(data):
		logging.debug("try_to_execute " + str(data))
		if not Command.validate(data):
			return "Invalid command: forbidden character found"
		
		logging.debug("executing " + data)
		stdout = Command.execute(data)
		return stdout


class ThreadedSocket:
	"""
	Referência: stackoverflow.com/a/23828265
	"""
	
	def __init__(self, args):
		# TODO remover hardcoded hostname
		self.hostname = "localhost"
		self.port = args.port

		self.skt = socket.socket()
		self.skt.bind( (self.hostname, self.port) )
		
		logging.debug("inited")


	def listenClient(conn, addr):
		conn.settimeout(2)
		while True:
			try:
				encoded_data = conn.recv(1024)
				logging.debug("received " + str(encoded_data))
				if not encoded_data:
					logging.debug("data is None?!")
					raise Exception("data is None?!")

				logging.debug("decoding")
				decoded_data = protocol.decode(encoded_data) 
				logging.debug("decoded data: " + str(decoded_data))
				response_msg = Command.try_to_execute(" ".join(decoded_data))
				logging.debug("stdout: " + response_msg)
			except AssertionError:
				response_msg = "failed checksum while decoding request"
				logging.debug(response_msg)
			except:
				e = sys.exc_info()[0]
				response_msg = str(e)
			finally:
				response = protocol.encode_response("", response_msg, conn.getsockname()[0], addr[0])
				logging.debug("sending " + str(response))
				conn.send(response)
				conn.close()
				logging.debug("sent and closed connection to " + str(addr))
				break


	def listen(self):
		self.skt.listen()

		while True:
			conn, addr = self.skt.accept()
			conn.settimeout(3)
			threading.Thread(target=ThreadedSocket.listenClient, args=(conn, addr)).start()
			
		self.skt.close()

	

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser()
	parser.add_argument("port", help="port on which to run the daemon", type=int)

	args = parser.parse_args()

	logging.basicConfig(filename=config['logging']['daemon'] % str(args.port), level=logging.DEBUG)

	ThreadedSocket(args).listen()
