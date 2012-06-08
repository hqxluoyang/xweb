'''
Created on 2012-6-3

@author: lifei
'''

import sys
from controller import XController
import inspect
from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader
from werkzeug.exceptions import NotFound, HTTPException #@UnresolvedImport
import logging
from web import XRequest, XResponse

class CommitFailedError(Exception):
    pass

class XProcess:

    def __init__(self, app, environ, start_response):
        self.environ = environ
        self.app = app
        self.start_response = start_response

    def __rewrite(self):
        adapter = self.app.url_map.bind_to_environ(self.environ)
        q, values = adapter.match()
        
        if q:
            if self.environ['QUERY_STRING']:
                self.environ['QUERY_STRING'] += '&'+q
            else:
                self.environ['QUERY_STRING'] = q
    
        self.request = XRequest(self.environ, populate_request=False)
        
        if values:
            self.request.context.update(values)
            
        return True
        
            
    def __process(self):
        
        controller  = self.request.get('c')
        action      = self.request.get('a')

        if controller and action:
            controller = controller.lower()
            action = action.lower()
            controller_module_path = 'controllers.%s'%controller
            if controller == 'default':
                controller_module_path = 'controllers'
            controller_module = sys.modules.get(controller_module_path)
            try:
                if not controller_module:
                    controller_module = __import__(controller_module_path)

                controller_class_name = controller.title().replace('_', '') + 'Controller'
                if not hasattr(controller_module, controller_class_name):
                    return NotFound()
                    
                controller_class = getattr(controller_module, controller_class_name)

                controller_instance = controller_class(self.request)

                if isinstance(controller_instance, XController):
                    action_method = getattr(controller_instance, 'action_'+action)
                    spec = inspect.getargspec(action_method.__func__)
                    func_args = spec.args
                    defaults = spec.defaults
                    
                    kwargs = {}
                    if defaults and func_args:
                        func_args = list(func_args)
                        defaults = list(defaults)
                        
                        for i in range(len(func_args)-len(defaults)): #@UnusedVariable
                            defaults.insert(0, None)
                                
                        for func_arg, arg in zip(func_args, defaults):
                            if not self.request.args.has_key(func_arg):
                                kwargs[func_arg] = arg
                            else:
                                kwargs[func_arg] = self.request.args.get(func_args)
                    
                    controller_instance.before()       
                    action_method(**kwargs)
                    controller_instance.after()
                    
                    try:
                        unitofwork = controller_instance.unitofwork
                        unitofwork.commit()
                    except:
                        unitofwork.rollback()
                        raise CommitFailedError()
                    
                    
                    context = controller_instance.context

                    if controller_instance.context['code'] == 200:
                        if controller_instance.context['type'] == 'html':
                            template_path = "templates/%s"%controller
                            jinja_env = Environment(loader=FileSystemLoader(template_path), autoescape=True)
                            t = jinja_env.get_template(action + '.html')
                            return XResponse(t.render(context), mimetype='text/html')
                        elif controller_instance.context['type'] == 'json':
                            return XResponse(context['json'], mimetype='application/json')
                        elif controller_instance.context['type'] == 'string':
                            return XResponse(context['string'], mimetype='text/html')
                        else:
                            pass
                    elif controller_instance.context['code'] == 302:
                        pass
                    elif controller_instance.context['code'] == 301:
                        pass
                    elif controller_instance.context['code'] == 400:
                        pass
                    elif controller_instance.context['code'] == 401:
                        pass
                    elif controller_instance.context['code'] == 402:
                        pass
                    elif controller_instance.context['code'] == 403:
                        pass
                    elif controller_instance.context['code'] == 404:
                        pass
                    else:
                        pass
#            except ImportError, AttributeError:
#                return NotFound()
                
            except Exception as ex:
                logging.exception(ex)
                return XResponse(str(ex), mimetype='text/html')
        
        return NotFound()

    def run(self):
        response = None
        try:
            if self.__rewrite():
                response = self.__process()
        except HTTPException, ex:
            response = ex
        
        if response:
            return response(self.environ, self.start_response)