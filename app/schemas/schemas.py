# app/schemas/schemas.py
# Pattern: Schema/DTO — validates and serializes request/response data

from marshmallow import Schema, fields, validate, validates, ValidationError, post_load


class RegisterSchema(Schema):
    full_name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email     = fields.Email(required=True)
    password  = fields.Str(required=True, validate=validate.Length(min=6, max=128))

    @validates('full_name')
    def validate_name(self, value):
        if not value.strip():
            raise ValidationError('Name cannot be empty')


class LoginSchema(Schema):
    email    = fields.Email(required=True)
    password = fields.Str(required=True)


class ScriptCreateSchema(Schema):
    title              = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    raw_text           = fields.Str(required=True, validate=validate.Length(min=10))
    audience_type      = fields.Str(load_default='General',
                                    validate=validate.OneOf([
                                        'General','Executives','Investors',
                                        'Students','Media','Clients','Wedding'
                                    ]))
    estimated_duration = fields.Int(load_default=0, validate=validate.Range(min=0))


class ScriptUpdateSchema(Schema):
    title              = fields.Str(validate=validate.Length(min=1, max=200))
    raw_text           = fields.Str(validate=validate.Length(min=10))
    audience_type      = fields.Str(validate=validate.OneOf([
                             'General','Executives','Investors',
                             'Students','Media','Clients','Wedding'
                         ]))
    estimated_duration = fields.Int(validate=validate.Range(min=0))


class SessionStartSchema(Schema):
    script_id = fields.Int(load_default=None, allow_none=True)


class PostureEventSchema(Schema):
    event_type        = fields.Str(required=True, validate=validate.OneOf([
                            'slouch','crossed_arms','confident_gesture','eye_contact'
                        ]))
    timestamp_seconds = fields.Float(required=True, validate=validate.Range(min=0))
    duration_seconds  = fields.Float(load_default=0.0, validate=validate.Range(min=0))


class SessionFinishSchema(Schema):
    duration_seconds = fields.Int(required=True, validate=validate.Range(min=1))
