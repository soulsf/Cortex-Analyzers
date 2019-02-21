#!/usr/bin/env python
# encoding: utf-8

from cortexutils.responder import Responder
from rtkit.resource import RTResource
from rtkit.authenticators import CookieAuthenticator
from rtkit.errors import RTResourceError

from rtkit import set_logging
import logging
import re

set_logging('debug')
logger = logging.getLogger('rtkit')


class RT(Responder):
    def __init__(self):
        Responder.__init__(self)
        self.rt_url = self.get_param('config.rt_url', '')
        self.rt_user = self.get_param('config.rt_user', '')
        self.rt_queue= self.get_param('config.rt_queue', '')
        self.rt_subject= self.get_param('config.rt_subject', '')
        self.rt_thid= self.get_param('config.rt_thid', 'internal ID')
        self.rt_pw = self.get_param('config.rt_pw', None, '')

        self.resource = RTResource(self.rt_url, self.rt_user, self.rt_pw, CookieAuthenticator)


    def run(self):
        Responder.run(self)

        title = self.get_param('data.title', None, 'title is missing')
        title = title.encode('utf-8')

        description = self.get_param('data.description', None, 'description is missing')
        description = description.encode('utf-8')

        if self.data_type == 'thehive:case':
            # Search requestor in custom field rt_req
            req = self.get_param('data.customFields.rt_req.string', None, 'requestor not found in customfield rt_req')
            if req:
                req = req
            else:
                self.error('requestor not found in customfield rt_req')
        else:
            self.error('Invalid dataType')

        caseid = self.get_param('data._id')
        casenr = str(self.get_param('data.caseId'))
        subject = self.rt_subject

        if '__thehivetitle__' in subject:
            subject = subject.replace('__thehivetitle__', title)

        if '__thehivecaseid__' in subject:
            subject = subject.replace('__thehivecaseid__', casenr)

        content = {
            'content': {
            'Queue': self.rt_queue,
            'Subject' : subject,
            'Requestor': req,
            'CF.{'+self.rt_thid+'}' : caseid
            }
            }
        try:
            response = self.resource.post(path='ticket/new', payload=content,)
            r = str(response.parsed[0])
            id = re.findall(r'\d+',r)
        except RTResourceError as e:
            logger.error(e.response.status_int)
            logger.error(e.response.status)
            logger.error(e.response.parsed)
        self.report({'rt_ticket' : id[0]})

    def operations(self, raw):
        return [self.build_operation('AddTagToCase', tag='rt_ticket:{}'.format(raw['rt_ticket']))]


if __name__ == '__main__':
    RT().run()
