from xweb.mvc.controller import *
from xweb.config import XConfig
from werkzeug.exceptions import NotFound, HTTPException #@UnresolvedImport
from xweb.mvc.web import XResponse

from domain import Video, StopTime


class DefaultController(XController):

    @settings(mimetype='xml')
    def doIndex(self):

        self.echo("hehe")
        import time
        self.context['user'] = time.time()
        
        for i in range(1000):
            self.secure_cookies[i] = i*i 

        self.context['link'] = self.createUrl('default/long', short_id=110000L)
        
        s = StopTime.get(train_code='01000000Z202', station_no=1)
        s.distance = 0
        
        video = Video.get(1000000100)
        video.title = time.time()
        video.category_id = 0
        
        self.context['stops'] = StopTime.getAllByCond('1=1 limit 10')
       
    def doHelp(self):
        self.echo("hello world")
        
        
    @settings(mimetype='text')
    def doShort(self):
        self.echo("<a href=%s>hehe</a>" % self.createUrl('default/short', short_id=110000L))
        self.mimetype = 'text/xhtml'
        
    @settings(status_code=500)
    def handleException(self, **kwargs):
        ex = kwargs.get('ex')
        assert isinstance(ex, Exception)
        self.response.data = str(ex)
        
        if self.app.use_debuger:
            raise
