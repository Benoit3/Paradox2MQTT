#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading,signal
import configparser
import itertools
import logging, logging.config
import ParadoxPanel,PRT3Zone,PRT3Area
import paho.mqtt.client as mqtt
import time
import json
import re



def on_connect(client, userdata, flags, rc):
	#subscribe to Utility Key messages with Q0s of 2
	client.subscribe(mqttTopicRoot+'/UK/+',2);
	client.subscribe(mqttTopicRoot+'/area/+/set',2);
	logger.critical('Connected to MQTT broker');
	
	#loop on areas and pusblish its status
	for area in panel.area:
			area.onChangeCallback();
	#loop on zones and pusblish its status
	for zone in panel.zone:
			zone.onChangeCallback();
			
def on_disconnect(client, userdata, rc):
	logger.critical('Diconnected from MQTT broker');

def utilityKey(client, userdata, message):
	logger.info('IK MQTT message: '+message.topic+':'+str(message.payload))
	
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
		
def arm(client, userdata, message):
	logger.info('Arm MQTT message: '+message.topic+':'+str(message.payload))
	
	#to get traceback in case of error in the mqtt thread
	try:
		#check message structure and get area to arm id
		RE_TOPIC_FILTER = re.compile(mqttTopicRoot+r"/area/(\d)/set");
		matchTopicFilter = RE_TOPIC_FILTER.match(message.topic);

		#if the area id is correct
		if (matchTopicFilter):
			areaId=(int)(matchTopicFilter.groups()[0])
			#get requested status
			try:
				cmd=PRT3Area.AreaArmStatus(message.payload.decode('UTF-8'));
			except ValueError:
				logger.warning('unknown Area arm request :' + message.payload.decode('UTF-8'))
				return
			if ( 0<areaId and areaId <9) :
				#arm requested area
				panel.area[areaId-1].armDisarm(cmd,pin);
				
	except BaseException as exc:
		logger.exception(exc);

def publish(topic,payload):
	#if the topic is not in the cache or payload need to be updated
	if ((topic not in mqttCache) or (mqttCache[topic]['payload']!=payload)):
			mqttCache[topic]={'payload':payload};
			client.publish(mqttTopicRoot+topic,payload,1,True);

def areaPublish(self):
	value={'id':self.id,'name':self.name,'status':str(self.status.value),'memory':self.memory,'trouble':self.trouble,'ready':self.ready,'alarm':self.alarm};
	publish('/area/'+str(self.id),json.dumps(value));
	
   
def zonePublish(self):
	value={'id':self.id,'name':self.name,'status':str(self.status.value),'alarm':self.alarm,'fireAlarm':self.fireAlarm};
	publish('/zone/'+str(self.id),json.dumps(value));
	
def sigterm_exit(signum, frame):
		logger.critical('Stop requested by SIGTERM, raising KeyboardInterrupt');
		raise KeyboardInterrupt;	
	
if __name__ == '__main__':

	# Initialisation Logger
	logging.config.fileConfig('logging.conf');
	logger = logging.getLogger(__name__);
	
	#Sigterm trapping
	signal.signal(signal.SIGTERM, sigterm_exit);
	
	#MQTT message cache creation
	mqttCache=dict();
	
	try:
		#Initialisation config
		config = configparser.ConfigParser()
		config.read('Paradox2MQTT.conf')
		serialPort=config.get('Serial','port');
		baudrate=config.get('Serial','baudrate');
		logger.critical('Serial port configuration: '+serialPort+' baudrate: '+baudrate);

		#MQTT settings
		mqttBrokerHost=config.get('MQTT','brokerHost');
		mqttBrokerPort=config.get('MQTT','brokerPort');
		mqttTopicRoot=config.get('MQTT','topicRoot');
		logger.critical('Broker: '+mqttBrokerHost+' : '+mqttBrokerPort);
		logger.critical('Topic Root: '+mqttTopicRoot);
		

		
		#init panel
		areaNb=int(config.get('Panel','areaNb'));
		zoneNb=int(config.get('Panel','zoneNb'));
		userNb=int(config.get('Panel','userNb'));
		pin=config.get('Panel','pin');
		panel=ParadoxPanel.ParadoxPanel(areaNb,zoneNb,userNb,serialPort,baudrate);
		PRT3Zone.Zone.onChangeCallback=zonePublish;
		PRT3Area.Area.onChangeCallback=areaPublish;
		
		#init mqtt brooker
		client = mqtt.Client()
		client.on_connect = on_connect
		client.on_disconnect = on_disconnect
		client.will_set(mqttTopicRoot+'/comStatus',"Offline",1,True)
		client.connect_async(mqttBrokerHost, int(mqttBrokerPort))
		client.message_callback_add(mqttTopicRoot+'/UK/+',utilityKey)
		client.message_callback_add(mqttTopicRoot+'/area/+/set',arm)
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
				
				#refresh panel objects, one every 10s
				item.requestRefresh();
				time.sleep(5);
				if not item.statusAvailable:
					errorCounter+=1;
					#with 3 successive error
					if (errorCounter>=3):
						if comStatus:
							client.publish(mqttTopicRoot+'/comStatus','Error',1,True);
							comStatus=False;
						panel.prt3.reconnect();
						errorCounter=0;
						
				else:
					errorCounter=0;
					if not comStatus:
						client.publish(mqttTopicRoot+'/comStatus','OK',1,True);
						comStatus=True;
				time.sleep(5);
				#check that all threads are living
				if (threading.active_count() < 3):
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
		
			



	
		

  










