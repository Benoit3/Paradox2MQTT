#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import threading
import re

from enum import Enum


class AreaArmStatus(Enum):
    DISARMED = "D"
    ARMED = "A"
    FORCEARMED = "F"
    STAYARMED = "S"
    INSTANTARMED = "I"

class Area:
	prt3=None;
	logger=None;
	onChangeCallback=None;

	@classmethod
	def initAreaList(cls,area,prt3):
		cls.prt3=prt3;
		cls.logger=logging.getLogger('Area');
		
		for i,val in enumerate(area):
			#initialisation
			area[i]=Area(i+1);
			area[i].requestRefresh();	
		
	@classmethod
	def processPRT3Reply(cls,area,line):
		match=re.compile(r"(?:RA|AL)(\d\d\d).{0,16}").match(line);
		if (match):
			index=(int)(match.groups()[0]);	
			try:
				#warning Area i info are saved in area [i-1]
				area[index-1].updateFromPRT3(line);
			except IndexError:
				cls.logger.warning('Area index error: '+str(index-1));	
			return True;
		else:
			return False;

	def stateLog(self):
			log='update area : '+str(self.id)+' '+str(self.name)+' Status: '+str(self.status.name)+' Ready: '+str(self.ready)+' Alarm: '+str(self.alarm)+' Memory: '+str(self.memory);
			self.logger.info(log);
		
	@property
	def status(self):
			return self._status;
			
	@status.setter
	def status(self,x):
		if (x!=self._status):
			self._status=x;
			self.stateLog();
			
	@property
	def memory(self):
			return self._memory;
			
	@memory.setter
	def memory(self,x):
		if (x!=self._memory):
			self._memory=x;
			self.stateLog();
			
	@property
	def ready(self):
			return self._ready;
			
	@ready.setter
	def ready(self,x):
		if (x!=self._ready):
			self._ready=x;
			self.stateLog();
			
	@property
	def alarm(self):
			return self._alarm;
			
	@alarm.setter
	def alarm(self,x):
		if (x!=self._alarm):
			self._alarm=x;
			self.stateLog();
	
	def timeout(self):
		self.logger.error('Area '+str(self.id)+' answer timeout');
		self.statusAvailable=False;
	
	def __init__(self,index):
		self.logger.debug('create Area: '+str(index));
		self.id=index;
		self.name='';
		self._status=AreaArmStatus.DISARMED;
		self._memory=False;
		self.trouble=False;
		self._ready=False;
		self._alarm=False;
		self.refreshTimer=None;
		self.statusAvailable=False;
	
			
	def requestRefresh(self):
		#send label request to PRT3.
		self.prt3.send("AL{0:0>3}".format(self.id));
		self.requestRefreshStatus();
		
		#wait for timer expiration or cancelation
		self.refreshTimer.join();
		
	def requestRefreshStatus(self):
		#(re)arm timer if not already running
		if (self.refreshTimer is None) or (not self.refreshTimer.is_alive()):
			self.refreshTimer=threading.Timer(2.0,self.timeout);
			self.refreshTimer.start();
		
		#send status request to PRT3.
		self.prt3.send("RA{0:0>3}".format(self.id));
		
	def updateFromPRT3(self,answer):
		RE_REQUEST_AREA_STATUS_REPLY = re.compile(r"RA(\d\d\d)(\w)\w\w(\w)\w(\w)\w");
		RE_REQUEST_AREA_LABEL_REPLY = re.compile(r"AL(\d\d\d)(.{0,16})");
		RE_REQUEST_AREA_FAILED_REPLY = re.compile(r"(?:RA|AL)(\d\d\d)&fail");
		matchAreaStatusRequestReply = RE_REQUEST_AREA_STATUS_REPLY.match(answer);
		matchAreaLabelRequestReply = RE_REQUEST_AREA_LABEL_REPLY.match(answer);
		matchAreaFailedReply = RE_REQUEST_AREA_FAILED_REPLY.match(answer);
		
		#if label reply with failed info
		if (matchAreaFailedReply and ((int)(matchAreaFailedReply.groups()[0])==self.id)):
			self.logger.warning('update Area : '+str(self.id)+' failed');
			return True;
			
		#if status reply with id correct
		elif (matchAreaStatusRequestReply and ((int)(matchAreaStatusRequestReply.groups()[0])==self.id) ):
			
			#cancel waiting timer
			self.refreshTimer.cancel();
			
			#update of Arm status
			self.status=AreaArmStatus(matchAreaStatusRequestReply.groups()[1]);
			
			#update of Ready status
			self.ready = (matchAreaStatusRequestReply.groups()[2]=='O');
			
			#update of Alarm status
			self.alarm = (matchAreaStatusRequestReply.groups()[3]=='A');
			
			#onchange callback call
			if (self.onChangeCallback != None):
				self.onChangeCallback();
				
			#flag status as availvale
			self.statusAvailable=True;
			
			return True;
			
		#if label reply with id correct
		elif (matchAreaLabelRequestReply and ((int)(matchAreaLabelRequestReply.groups()[0])==self.id)):
			self.name=matchAreaLabelRequestReply.groups()[1].rstrip();
			
			self.logger.info('update area : '+str(self.id)+' Label: '+str(self.name));
			return True;

		#in case of no match
		else:
			#return False as reply parsing is OK
			return False;

	def armDisarm(self,cmd,pin):
		RE_ARM_AREA_PIN = re.compile(r"^(\d{4,6})$");
		if RE_ARM_AREA_PIN.match(pin):
			#if disarm request
			if cmd==AreaArmStatus.DISARMED:
				self.prt3.send("AD{0:0>3}".format(self.id)+pin);
				self.logger.info('Send disarm request Area :'+str(self.id));
			else:
			#send request to PRT3.
				self.prt3.send("AA{0:0>3}".format(self.id)+cmd.value+pin);
				self.logger.info('Send arm request; type :'+str(cmd)+' Area :'+str(self.id));
		else:
			self.logger.warning('wrong pin format '+pin);

	
		

  










