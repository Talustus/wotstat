#!/usr/bin/python
# -*- coding: utf-8 -*-

import BigWorld
from Account import Account
from adisp import process
from items import vehicles as vehicles_core
from gui.shared.utils.requesters import StatsRequester
from gui.shared import g_itemsCache
from notification.NotificationListView import NotificationListView
from messenger.formatters.service_channel import BattleResultsFormatter
from debug_utils import *

@process
def getDossier(callback):
    stats = {}
    stats['credits'] = yield StatsRequester().getCredits()
    dossier = g_itemsCache.items.getAccountDossier().getTotalStats()
    stats['battlesCount'] = dossier.getBattlesCount()
    stats['winsCount'] = dossier.getWinsCount()
    stats['totalXP'] = dossier.getXP()
    stats['damageDealt'] = dossier.getDamageDealt()
    stats['fragsCount'] = dossier.getFragsCount()
    stats['spottedCount'] = dossier.getSpottedEnemiesCount()
    stats['dCapPoints'] = dossier.getDroppedCapturePoints()
    callback(stats)

def createMessage(text):
    msg = {
        'type': 'black',
        'icon': '../maps/icons/library/PersonalAchievementsIcon-1.png',
        'message': text,
        'showMore': {
            'command': 'stat',
            'enabled': False,
            'param': 'None'
        }
    }
    message = {
        'message': msg,
        'priority': True,
        'notify': False,
        'auxData': ['GameGreeting']
    }
    return message

class SessionStatistic(object):
    loaded = False

    def __init__(self):
        self.startValues = {}
        self.lastValues = {}
        self.values = {}

    def load(self):
        if not self.loaded:
            getDossier(self.startValues.update)
            self.loaded = True

    def updateDossier(self):
        getDossier(self.lastValues.update)

    def recalc(self):
        for key in self.startValues.keys():
            self.values[key] = self.lastValues[key] - self.startValues[key]

    def getValue(self, name, default = 0):
        return str(self.values.get(name, default))

    def printMessage(self):
        self.recalc()
        return 'Credits: ' + self.getValue('credits')


old_onBecomePlayer = Account.onBecomePlayer

def new_onBecomePlayer(self):
    old_onBecomePlayer(self)

Account.onBecomePlayer = new_onBecomePlayer


old_nlv_populate = NotificationListView._populate

def new_nlv_populate(self, target = 'SummaryMessage'):
    old_nlv_populate(self)
    stat.load()
    stat.updateDossier()
    msg = createMessage(stat.printMessage())
    self.as_appendMessageS(msg)

NotificationListView._populate = new_nlv_populate

old_brf_format = BattleResultsFormatter.format

def new_brf_format(self, message, *args):
    result = old_brf_format(self, message, *args)
    vehicleCompDesc = message.data.get('vehTypeCompDescr', None)
    LOG_NOTE(vehicleCompDesc)
    vt = vehicles_core.getVehicleType(vehicleCompDesc)
    LOG_NOTE(vt.shortUserString)
    return result

BattleResultsFormatter.format = new_brf_format

stat = SessionStatistic()
