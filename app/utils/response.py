from flask import jsonify

def ok(data=None, msg='OK', status=200):
    body = {'success': True, 'message': msg}
    if data is not None: body['data'] = data
    return jsonify(body), status

def created(data=None, msg='Created'):
    return ok(data, msg, 201)

def err(msg, status=400):
    return jsonify({'success': False, 'message': msg}), status

def not_found(msg='Not found'):   return err(msg, 404)
def unauth(msg='Unauthorized'):   return err(msg, 401)
def conflict(msg='Conflict'):     return err(msg, 409)
