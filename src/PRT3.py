#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading
import logging
import serial.threaded


class PRT3:
	portIdentifier=None; #serial port id
	baudrate=None;
	transport = None;
	protocol = None;
	onReceive=None; #callback to process received lines

	def __init__(self,port,baudrate,onReceive):
		#logger
		self.logger = logging.getLogger(__name__)
		
		self.portIdentifier=port;
		self.baudrate=baudrate;
		self.onReceive=onReceive;
		self.connect();
		
	def connect(self):
		
		#open serial port
		self.port = serial.Serial(self.portIdentifier, baudrate=self.baudrate);
		#remind context for below internal class
		outer=self;
		
		class SerialConnector(serial.threaded.LineReader):
			TERMINATOR = b'\r';
			ENCODING='cp850';
			def handle_line(self, line):
				outer.logger.debug('Received line: '+line);
				
				#to get traceback in case of error in the serial thread
				try:
					outer.onReceive(line);
				except BaseException as exc:
					outer.logger.exception(exc)

				
			def connection_made(self, transport):
				print("Connection established");

			def connection_lost(self, exc):
				print("Connection lost");
				#print(repr(exc));

				

		self.connector = serial.threaded.ReaderThread(self.port,SerialConnector);
		self.connector.start();
		self.transport, self.protocol = self.connector.connect();

	def send(self,line):
			line_r=line+'\r';
			self.logger.debug('Sending command: '+line);
			self.port.write(line_r.encode('cp850'));
			return(True);



