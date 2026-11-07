"""Validator for the explicit JSON Schema subset used by this repository.

Unsupported keywords fail closed; no schema fetching or runtime dependencies.
Semantic checks (references, hash chains) remain in the domain validators.
"""
from datetime import date
import re

KEYWORDS = {'$schema','$id','title','description','type','const','enum','required','properties',
            'additionalProperties','items','minLength','pattern','minimum','maximum','uniqueItems',
            'format','anyOf','not'}


def validate(value, schema, path='$'):
    unknown = set(schema)-KEYWORDS
    if unknown:
        raise ValueError(f'unsupported schema keywords: {sorted(unknown)}')
    if 'type' in schema:
        kinds = schema['type'] if isinstance(schema['type'],list) else [schema['type']]
        checks = {'object':isinstance(value,dict),'array':isinstance(value,list),'string':isinstance(value,str),
                  'integer':type(value) is int,'number':type(value) in (int,float),'boolean':type(value) is bool,'null':value is None}
        if not any(checks.get(kind,False) for kind in kinds):
            raise ValueError(f'{path}: wrong type')
    if 'const' in schema and (type(value) != type(schema['const']) or value != schema['const']):
        raise ValueError(f'{path}: wrong constant')
    if 'enum' in schema and not any(type(value) is type(x) and value == x for x in schema['enum']):
        raise ValueError(f'{path}: wrong enum value')
    if 'not' in schema:
        try: validate(value,schema['not'],path)
        except ValueError: pass
        else: raise ValueError(f'{path}: forbidden value')
    if 'anyOf' in schema:
        for option in schema['anyOf']:
            try: validate(value,option,path);break
            except ValueError: pass
        else: raise ValueError(f'{path}: no matching variant')
    if isinstance(value,dict):
        if set(schema.get('required',[]))-set(value):
            raise ValueError(f'{path}: missing required property')
        properties=schema.get('properties',{})
        for key,item in value.items():
            if key in properties:validate(item,properties[key],path+'.'+key)
            elif schema.get('additionalProperties') is False:raise ValueError(f'{path}: unknown property {key}')
            elif isinstance(schema.get('additionalProperties'),dict):validate(item,schema['additionalProperties'],path+'.'+key)
    if isinstance(value,list):
        for i,item in enumerate(value):validate(item,schema.get('items',{}),f'{path}[{i}]')
        if schema.get('uniqueItems') and any(item in value[:i] for i,item in enumerate(value)):
            raise ValueError(f'{path}: duplicate item')
    if isinstance(value,str):
        if len(value)<schema.get('minLength',0) or ('pattern' in schema and re.search(schema['pattern'],value) is None):
            raise ValueError(f'{path}: invalid string')
        if schema.get('format')=='date':date.fromisoformat(value)
    if type(value) in (int,float):
        if ('minimum' in schema and value<schema['minimum']) or ('maximum' in schema and value>schema['maximum']):
            raise ValueError(f'{path}: number out of range')
    return value
