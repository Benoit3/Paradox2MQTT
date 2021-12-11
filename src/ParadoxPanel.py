#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import PRT3,PRT3Event,PRT3Zone,PRT3Area,PRT3User,PRT3UtilityKey
 
class ParadoxPanel:
	area=None;
	def __init__(self,areaNb=8,zoneNb=192,userNb=999,serialPort='/dev/ttyUSB0',baudrate=57600):
		
		#logger
		self.logger = logging.getLogger(__name__)
		
		#object list creation
		self.zone=[PRT3Zone.Zone]*(zoneNb);
		self.user=[PRT3User.User]*(userNb);
		self.area=[PRT3Area.Area]*(areaNb);
		
		#connection to the panel
		self.prt3=PRT3.PRT3(serialPort,baudrate,self.processMessage);
				
		#init Areas
		PRT3Area.Area.initAreaList(self.area,self.prt3);

		#init Zones
		PRT3Zone.Zone.initZoneList(self.zone,self.prt3);

		#init Users
		PRT3User.User.initUserList(self.user,self.prt3);
		
		#init Utility Keys
		self.utilityKey=PRT3UtilityKey.UtilityKey(self.prt3);
			
	def processMessage(self,strData):
		events = PRT3Event.interprete(strData);
		if (PRT3Area.Area.processPRT3Reply(self.area,strData)):
			pass
		elif (PRT3Zone.Zone.processPRT3Reply(self.zone,strData)):
			pass
		elif (PRT3User.User.processPRT3Reply(self.user,strData)):
			pass
				
		elif (events == None):
			print("Received [{0}] unhandled message".format(strData.replace("\r", "<cr>")))
		else :
			self.EventUpdateDevice(events)
			
	def EventUpdateDevice(self,events):


		for event in events :
			#area to be refreshed
			if (event.group in PRT3Event.AREA_EVENT):
				#warning area i is at index i-1 in the list
				self.area[event.area-1].requestRefreshStatus();
				
			#zone to be refreshed
			if (event.group in PRT3Event.ZONE_EVENT):
				#warning area i is at index i-1 in the list
				self.area[event.area-1].requestRefreshStatus();
				#warning zone i is at index i-1 in the list
				self.zone[event.number-1].requestRefreshStatus();
		return            
