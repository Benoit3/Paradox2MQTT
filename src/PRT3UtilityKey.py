#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

class UtilityKey:
	prt3=None;
	logger=None;
	
	def __init__(self,prt3):
		self.logger=logging.getLogger('UtilityKey');
		self.prt3=prt3;
		
	def activate(self,keyId):
		#send utility key request to PRT3
		self.logger.info('Activate Utility Key: '+str(keyId));
		self.prt3.send("UK{0:0>3}".format(keyId));

