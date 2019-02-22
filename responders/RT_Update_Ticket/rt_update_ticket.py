#!/usr/bin/env python
# encoding: utf-8

from cortexutils.responder import Responder
from rtkit.resource import RTResource
from rtkit.authenticators import CookieAuthenticator
from rtkit.errors import RTResourceError

from rtkit import set_logging
import logging
import re

set_logging('info')
logger = logging.getLogger('rtkit')


class RT(Responder):
    def __init__(self):
        Responder.__init__(self)
        self.rt_url = self.get_param('config.rt_url', '')
        self.rt_user = self.get_param('config.rt_user', '')
        self.rt_queue= self.get_param('config.rt_queue', '')
        self.rt_subject= self.get_param('config.rt_subject', '')
        self.rt_pw = self.get_param('config.rt_pw', None, '')

        self.resource = RTResource(self.rt_url, self.rt_user, self.rt_pw, CookieAuthenticator)


    def run(self):
        Responder.run(self)

        message = self.get_param('data.message', None, 'message is missing')
        message = message.encode('utf-8')

        if self.data_type == 'thehive:case_task_log':
            # Search RT Ticket ID in tags
            ticketid = None
            tags = self.get_param('data.case_task.case.tags', None, 'RT Ticket ID not found in tags')
            ticket_tags = [t[10:] for t in tags if t.startswith('rt_ticket:')]
            if ticket_tags:
                ticketid = ticket_tags.pop()
            else:
                self.error('RT Ticket ID not found in tags')

            content = {
                'content': {
                'Action': 'correspond',
                'Text' : message
                }
                }
            try:
                response = self.resource.post(path='ticket/'+str(ticketid)+'/comment', payload=content,)
                r = str(response.parsed[0])
            except RTResourceError as e:
                logger.error(e.response.status_int)
                logger.error(e.response.status)
                logger.error(e.response.parsed)
            self.report({'message': 'correspondance added'})
        else:
            self.error('Invalid dataType')

    def operations(self, raw):
        return [self.build_operation('AddTagToCase', tag='rt_communication')]


if __name__ == '__main__':
    RT().run()
    
