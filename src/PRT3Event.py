#!/usr/bin/env python
# -*- coding: utf-8 -*-

from enum import IntEnum
from enum import Enum
import re

#SYSTEM EVENT
RE_SYSTEM_EVENT = re.compile(r"G(\d\d\d)N(\d\d\d)A(\d\d\d)")

class SystemEventGroup(IntEnum):
	ZONE_OK = 0
	ZONE_OPEN = 1
	ZONE_TAMPERED = 2
	ZONE_FIRE_LOOP = 3
	ARMED_WITH_MASTERCODE = 9
	ARMED_WITH_USERCODE = 10
	ARMED_WITH_KEYSWITCH = 11
	ARMED_SPECIAL = 12
	DISARMED_WITH_MASTERCODE = 13
	DISARMED_WITH_USERCODE = 14
	DISARMED_WITH_KEYSWITCH = 15
	DISARMED_AFTERALARM_WITH_MASTERCODE = 16
	DISARMED_AFTERALARM_WITH_USERCODE = 17
	DISARMED_AFTERALARM_WITH_KEYSWITCH = 18
	ALARM_CANCELLED_WITH_MASTERCODE = 19
	ARMING_CANCELED_WITH_USERCODE = 20
	ZONE_BYPASSED=23
	ZONE_IN_ALARM=24
	FIRE_ALARM=25
	ZONE_ALARM_RESTORE=26
	FIRE_ALARM_RESTORE=27
	SPECIAL_ALARM=30
	DURESS_ALARM_BY_USER=31
	ZONE_SHUTDOWN=32
	ZONE_TAMPER =33
	ZONE_TAMPER_RESTORE=34
	TROUBLE_EVENT = 36
	TROUBLE_RESTORE = 37
	MODULE_TROUBLE = 38
	MODULE_TROUBLE_RESTORE = 39
	LOW_BATTERY_ON_ZONE = 41
	ZONE_SUPERVISION_TROUBLE = 42
	LOW_BATTERY_ON_ZONE_RESTORE = 43
	ZONE_SUPERVISION_TROUBLE_RESTORE = 44
	STATUS1 = 64
	STATUS2 = 65
	STATUS3 = 66



	@classmethod
	def has_value(cls, value):
		return any(value == item.value for item in cls)

	#Events with Area impact
	#Events with zone impact

ZONE_EVENT = {SystemEventGroup.ZONE_OK,
	SystemEventGroup.ZONE_OPEN,
	SystemEventGroup.ZONE_TAMPERED,
	SystemEventGroup.ZONE_FIRE_LOOP,
	SystemEventGroup.ZONE_IN_ALARM,
	SystemEventGroup.FIRE_ALARM,
	SystemEventGroup.ZONE_ALARM_RESTORE,
	SystemEventGroup.FIRE_ALARM_RESTORE		
	}
		   
AREA_EVENT = {SystemEventGroup.DISARMED_WITH_MASTERCODE,
	SystemEventGroup.DISARMED_WITH_USERCODE,
	SystemEventGroup.DISARMED_WITH_KEYSWITCH,
	SystemEventGroup.DISARMED_AFTERALARM_WITH_MASTERCODE,
	SystemEventGroup.DISARMED_AFTERALARM_WITH_USERCODE,
	SystemEventGroup.DISARMED_AFTERALARM_WITH_KEYSWITCH,
	SystemEventGroup.ARMED_WITH_MASTERCODE,
	SystemEventGroup.ARMED_WITH_USERCODE,
	SystemEventGroup.ARMED_WITH_KEYSWITCH,
	SystemEventGroup.ARMED_SPECIAL,
	SystemEventGroup.ZONE_IN_ALARM,
	SystemEventGroup.FIRE_ALARM,
	SystemEventGroup.ZONE_ALARM_RESTORE,
	SystemEventGroup.FIRE_ALARM_RESTORE		
	}

class Event(object):
    group = None
    number = None
    area = None
    
    def __str__(self):
        return "Group '%s' Number '%s' Area '%s'" % (self.group, self.number, self.area)
    
def interprete(line):
    event_to_return = Event()

    #system event handling
    matchSystemEvent = RE_SYSTEM_EVENT.match(line)
    if matchSystemEvent:
        group, number, area = matchSystemEvent.groups()
        group = int(group)
        number = int(number)
        area = int(area)

        if not SystemEventGroup.has_value(group):
            return None

        event_to_return.group = group
        event_to_return.number = number
        event_to_return.area = area
        return { event_to_return }

    return None
