#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import threading
import re

from enum import Enum

class User:
	area=None;
	prt3=None;
	logger=None;
	
	@classmethod
	def initUserList(cls,user,prt3):
		cls.prt3=prt3;
		cls.logger=logging.getLogger('User');
		
		for i,val in enumerate(user):
			#initialisation
			user[i]=User(i+1);
			user[i].requestInit();			
		
	@classmethod
	def processPRT3Reply(cls,user,line):
		match=re.compile(r"UL(\d\d\d).{0,16}").match(line);
		if (match):
			index=(int)(match.groups()[0]);
			try:
				user[index-1].updateFromPRT3(line);
			except IndexError:
				cls.logger.warning('User index error: '+str(index-1));	
			return True;
		else:
			return False;

	
	def __init__(self,index):
		self.logger.debug('create User: '+str(index));
		self.id=index;
		self.name='';
		self.initReady=threading.Event();
		
	def requestInit(self):
		#send label request to PRT3. Callback should be called before function return
		self.prt3.send("UL{0:0>3}".format(self.id));
		
		#wait for init
		self.initReady.wait(2.0);

	def updateFromPRT3(self,answer):
		RE_REQUEST_USER_LABEL_REPLY = re.compile(r"UL(\d\d\d)(.{0,16})");
		RE_REQUEST_USER_FAILED_REPLY = re.compile(r"UL(\d\d\d)&fail");
		matchUserLabelRequestReply = RE_REQUEST_USER_LABEL_REPLY.match(answer);
		matchUserFailedReply = RE_REQUEST_USER_FAILED_REPLY.match(answer);
		
		#if user reply with failed info
		if (matchUserFailedReply and ((int)(matchUserFailedReply.groups()[0])==self.id)):
			self.logger.warning('update User : '+str(self.id)+' failed');
			return True;
			
		elif (matchUserLabelRequestReply and ((int)(matchUserLabelRequestReply.groups()[0])==self.id)):
			self.name=matchUserLabelRequestReply.groups()[1].rstrip();
			self.logger.info('update User : '+str(self.id)+' Label: '+self.name);
			print('update User : '+str(self.id)+' Label: '+self.name);
			
			#release lock and return True as reply parsing is OK
			if (self.name!=''):
				self.initReady.set();
			return True;				
			
			#in case of no match
		else:
			return False;
