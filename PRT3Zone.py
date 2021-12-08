#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import threading
import re

from enum import Enum

class ZoneStatus(Enum):
		CLOSED = "C"
		OPEN = "O"
		TAMPERED = "T"
		FIRELOOP = "F"

class Zone:
	prt3=None;
	logger=None;
	onChangeCallback=None;
	
	@classmethod
	def initZoneList(cls,zone,prt3):
		cls.prt3=prt3;
		cls.logger=logging.getLogger('Zone');
		
		for i,val in enumerate(zone):
			#initialisation
			zone[i]=Zone(i+1);
			zone[i].requestRefresh();	
		
	@classmethod
	def processPRT3Reply(cls,zone,line):
		match=re.compile(r"(?:RZ|ZL)(\d\d\d).{0,16}").match(line);
		if (match):
			index=(int)(match.groups()[0]);
			try:
				zone[index-1].updateFromPRT3(line);
			except IndexError:
				cls.logger.warning('Zone index error: '+str(index-1));	
			return True;
		else:
			return False;
	

		
	def log(self):
			txt='update zone : '+str(self.id)+' '+str(self.name)+' Status: '+str(self.status.name)+' Alarm: '+str(self.alarm)+' FireAlarm: '+str(self.fireAlarm);
			self.logger.info(txt);
			print(txt);
						
	@property
	def status(self):
			return self._status;
			
	@status.setter
	def status(self,x):
		if (x!=self._status):
			self._status=x;
			self.log();
			

	@property
	def alarm(self):
			return self._alarm;
			
	@alarm.setter
	def alarm(self,x):
		if (x!=self._alarm):
			self._alarm=x;
			self.logger.info('update zone : '+str(self.id)+' '+str(self.name)+' Status: '+str(self.status.name)+' Alarm: '+str(self.alarm)+' FireAlarm: '+str(self.fireAlarm));
			print('update zone : '+str(self.id)+' '+str(self.name)+' Status: '+str(self.status.name)+' Alarm: '+str(self.alarm)+' FireAlarm: '+str(self.fireAlarm));
	
	@property
	def fireAlarm(self):
			return self._fireAlarm;
			
	@fireAlarm.setter
	def fireAlarm(self,x):
		if (x!=self._fireAlarm):
			self._fireAlarm=x;
			self.logger.info('update zone : '+str(self.id)+' '+str(self.name)+' Status: '+str(self.status.name)+' Alarm: '+str(self.alarm)+' FireAlarm: '+str(self.fireAlarm));
			print('update zone : '+str(self.id)+' '+str(self.name)+' Status: '+str(self.status.name)+' Alarm: '+str(self.alarm)+' FireAlarm: '+str(self.fireAlarm));

	def timeout(self):
		self.logger.error('Zone '+str(self.id)+' answer timeout');
		self.statusAvailable=False;
		
	def __init__(self,index):
		self.logger = logging.getLogger(__name__)
		self.logger.debug('create Zone: '+str(index));
		self.id=index;
		self.name='';
		self._status=ZoneStatus.OPEN;
		self._alarm=False;
		self._fireAlarm=False;
		self.refreshTimer=None;
		self.statusAvailable=False;	
				
	def requestRefresh(self):
		#send label request to PRT3.
		self.prt3.send("ZL{0:0>3}".format(self.id));
			
		#send status request to PRT3.
		self.requestRefreshStatus();
		
		#wait for timer expiration or cancelation
		self.refreshTimer.join();

	def requestRefreshStatus(self):
		#(re)arm timer if not already running
		if (self.refreshTimer is None) or (not self.refreshTimer.is_alive()):
			self.refreshTimer=threading.Timer(2.0,self.timeout);
			self.refreshTimer.start();
			
		#send status request to PRT3.
		self.prt3.send("RZ{0:0>3}".format(self.id));		

	def updateFromPRT3(self,answer):
		RE_REQUEST_ZONE_STATUS_REPLY = re.compile(r"RZ(\d\d\d)(\w)(\w)\w\w\w");
		RE_REQUEST_ZONE_LABEL_REPLY = re.compile(r"ZL(\d\d\d)(.{0,16})");
		RE_REQUEST_ZONE_FAILED_REPLY = re.compile(r"(?:RZ|ZL)(\d\d\d)&fail");
		matchZoneStatusRequestReply = RE_REQUEST_ZONE_STATUS_REPLY.match(answer);
		matchZoneLabelRequestReply = RE_REQUEST_ZONE_LABEL_REPLY.match(answer);
		matchZoneFailedReply = RE_REQUEST_ZONE_FAILED_REPLY.match(answer);
		
		#if zone reply with failed info
		if (matchZoneFailedReply and ((int)(matchZoneFailedReply.groups()[0])==self.id)):
			self.logger.warning('update Zone : '+str(self.id)+' failed');
				
			#return True as reply parsing is OK
			return True;
			
		#if status reply with id correct
		elif (matchZoneStatusRequestReply and ((int)(matchZoneStatusRequestReply.groups()[0])==self.id) ):
			
			#cancel waiting timer
			self.refreshTimer.cancel();
						
			#update of status
			self.status=ZoneStatus(matchZoneStatusRequestReply.groups()[1]);
			
			#update of Alarm status
			self.alarm = (matchZoneStatusRequestReply.groups()[1]=='A')
			self.fireAlarm = (matchZoneStatusRequestReply.groups()[2]=='F')
			
			#onchange callback call
			if (self.onChangeCallback != None):
				self.onChangeCallback();
							
			#flag status as availvale
			self.statusAvailable=True;
			
			return True;
			
		#if label reply with id correct
		elif (matchZoneLabelRequestReply and ((int)(matchZoneLabelRequestReply.groups()[0])==self.id)):
			self.name=matchZoneLabelRequestReply.groups()[1].rstrip();
			self.logger.info('update zone : '+str(self.id)+' Label: '+str(self.name));
			print('update zone : '+str(self.id)+' Label: '+str(self.name));
			return True;
		
		#in case of no match
		else:
			return False;



	
		

  










