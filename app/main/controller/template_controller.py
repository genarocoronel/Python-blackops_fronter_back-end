from flask_restplus import Resource
from flask import request
from app.main.service.template import TemplateView
from app.main.util.dto import TemplateDto
from app.main.util.decorator import token_required, user_has_permission

from flask import current_app as app


api = TemplateDto.api
_template = TemplateDto.template

@api.route('/editable')
class EditableTemplateList(Resource):
    @api.doc('list of editable templates')
    @api.marshal_list_with(_template)
    @token_required
    @user_has_permission('templates.view')
    def get(self):
        """ List all editable templates """        
        templates = TemplateView.list(edit=True)
        return templates

@api.route('/<public_id>/render')
@api.param('public_id', 'The Template Identifier')
@api.param('client_id', 'The Client Identifier')
@api.response(404, 'Template not found')
class TemplateRender(Resource):
    @api.doc('get template') 
    @token_required
    @user_has_permission('templates.view')
    def get(self, public_id): 
        """ Get template with provided identifier"""
        try:
            params = request.json

            view = TemplateView(public_id) 
            result = view.render_mail_content(params)     
            return result
        except Exception as err:
            api.abort(404, str(err))

@api.route('/<public_id>/send')
@api.param('public_id', 'The Template Identifier')
@api.param('client_id', 'The Client Identifier')
@api.response(404, 'Template not found')
class TemplateSend(Resource):
    @api.doc('send the template')
    @token_required
    @user_has_permission('templates.send')
    def post(self, public_id):
        """ Get template with provided identifier"""
        try:
            params = request.json

            view = TemplateView(public_id) 
            result = view.send_mail(params)     
            return result
        except Exception as err:
            api.abort(404, str(err))

