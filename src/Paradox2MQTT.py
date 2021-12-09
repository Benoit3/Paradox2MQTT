#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading,signal
import configparser
import itertools
import logging, logging.config
import PRT3,PRT3Event,PRT3Zone,PRT3Area,PRT3User,PRT3UtilityKey
import paho.mqtt.client as mqtt
import time
import json
import re


 
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

def on_connect(client, userdata, flags, rc):
	#subscribe to Utility Key messages with Q0s of 2
	client.subscribe(mqttTopicRoot+'/UK/+',2);
	logger.info('Connected to MQTT broker');
	
	#loop on areas and pusblish its status
	for area in panel.area:
			area.onChangeCallback();
	#loop on zones and pusblish its status
	for zone in panel.zone:
			zone.onChangeCallback();
			
def on_disconnect(client, userdata, rc):
	logger.critical('Diconnected from MQTT broker');

def utilityKey(client, userdata, message):
	logger.info('MQTT message: '+message.topic+':'+str(message.payload))
	
	#to get traceback in case of error in the mqtt thread
	try:
		#check message structure and get UK id
		RE_TOPIC_FILTER = re.compile(mqttTopicRoot+r"/UK/(\d{1,3})");
		matchTopicFilter = RE_TOPIC_FILTER.match(message.topic);

		#if the UK id is correct
		if (matchTopicFilter):
			UkId=(int)(matchTopicFilter.groups()[0])
			if ( 0<UkId and UkId <251) :
				#activate requested Utility Key
				panel.utilityKey.activate(UkId);
				
	except BaseException as exc:
		logger.exception(exc);

def areaPublish(self):
	value={'id':self.id,'name':self.name,'status':str(self.status.value),'memory':self.memory,'trouble':self.trouble,'ready':self.ready,'alarm':self.alarm};
	client.publish(mqttTopicRoot+'/area/'+str(self.id),json.dumps(value),1,True);
	
   
def zonePublish(self):
	value={'id':self.id,'name':self.name,'status':str(self.status.value),'alarm':self.alarm,'fireAlarm':self.fireAlarm};
	client.publish(mqttTopicRoot+'/zone/'+str(self.id),json.dumps(value),1,True);
	
def sigterm_exit(signum, frame):
		logger.critical('Stop requested by SIGTERM, raising KeyboardInterrupt');
		raise KeyboardInterrupt;	
	
if __name__ == '__main__':

	# Initialisation Logger
	logging.config.fileConfig('logging.conf');
	logger = logging.getLogger(__name__);
	
	#Sigterm trapping
	signal.signal(signal.SIGTERM, sigterm_exit);
	
	try:
		#Initialisation config
		config = configparser.ConfigParser()
		config.read('Paradox2MQTT.conf')
		serialPort=config.get('Serial','port');
		baudrate=config.get('Serial','baudrate');
		logger.info('Serial port configuration: '+serialPort+' baudrate: '+baudrate);

		#MQTT settings
		mqttBrokerHost=config.get('MQTT','brokerHost');
		mqttBrokerPort=config.get('MQTT','brokerPort');
		mqttTopicRoot=config.get('MQTT','topicRoot');
		logger.info('Broker: '+mqttBrokerHost+' : '+mqttBrokerPort);
		logger.info('Topic Root: '+mqttTopicRoot);	

		
		#init panel
		panel=ParadoxPanel(3,21,9,serialPort,baudrate);
		PRT3Zone.Zone.onChangeCallback=zonePublish;
		PRT3Area.Area.onChangeCallback=areaPublish;
		
		#init mqtt brooker
		client = mqtt.Client()
		client.on_connect = on_connect
		client.on_disconnect = on_disconnect
		client.will_set(mqttTopicRoot+'/comStatus',"Offline",1,True)
		client.connect_async(mqttBrokerHost, int(mqttBrokerPort))
		client.message_callback_add(mqttTopicRoot+'/UK/+',utilityKey)
		client.loop_start()
		
		#start loop
		run=True;
		
		#com status
		comStatus=True;
		errorCounter=0;
		client.publish(mqttTopicRoot+'/comStatus','OK',1,True);
		while run:
			#and iterate on panel items
			for item in itertools.chain(panel.area,panel.zone,panel.user):
				
				#check every 10s that all threads are living
				item.requestRefresh();
				time.sleep(10);
				if not item.statusAvailable:
					errorCounter+=1;
					#with 3 successive error
					if (errorCounter>=3):
						if comStatus:
							client.publish(mqttTopicRoot+'/comStatus','Error',1,True);
							comStatus=False;
						panel.prt3.reconnect();
						
				else:
					errorCounter=0;
					if not comStatus:
						client.publish(mqttTopicRoot+'/comStatus','OK',1,True);
						comStatus=True;
			
				#if not
				if (threading.active_count()!=3):
					#logging
					logger.critical(str(threading.active_count())+' thread(s) are living');
					#disconnect from mqtt server
					logger.critical('Disonnecting from MQTT broker');
					client.loop_stop();
					
					#disconnect from pr3t interface
					logger.critical('Closing serial port');
					panel.prt3.transport.close();
					
					run=False;
					break;
					
	except KeyboardInterrupt:
		logger.critical('Stopped by KeyboardInterrupt');
		
		#disconnect mqtt server
		logger.critical('Disonnecting from MQTT broker');
		client.loop_stop();
				
		#disconnect from pr3t interface
		logger.critical('Closing serial port');
		panel.prt3.transport.close();
	
	except BaseException as exc:	
		logger.exception(exc);
		
			



	
		

  










