import re

from ._parser_model import Param
import numbers

# objects
QUERYSPEC_REGEX = r"^(?P<name>\w+( +\w+)*)(\s+\((?P<type>[\w\[\]]+)\)?)?\s*(--(\s+((?P<required>required|optional)\.)?(?P<description>.*)?)?)?"
PARAM_MATCHER = re.compile(QUERYSPEC_REGEX,  re.IGNORECASE)
RESPONSE_REGEX = r"^((http\s+)?((?P<code>\d+)\s+))?response:$"
RESPONSE_MATCHER = re.compile(RESPONSE_REGEX,  re.IGNORECASE)
ERRORSPEC_REGEX = r"^(?P<code>\d+)\s*--\s*(?P<description>.*)$"
ERRORSPEC_MATCHER = re.compile(ERRORSPEC_REGEX, re.IGNORECASE)

#_PROP_SPEC_REGEX = re.compile("(?P<name>\w+): (?P<value>\w[\w\s]*)")}

class number(numbers.Number):
    def __new__(cls, val):
        if str(val).find('.'):
            try:
                return float(val)
            except ValueError:
                return val
        try:
            return int(val)
        except ValueError:
            return val
            
        

_PROPS_TYPE_LOOKUP = {
    bool: ('exclusiveMinimum', 'exclusiveMaximum', 'uniqueItems'),
    number: ('minimum', 'maximum', 'multipleOf', 'minItems', 'maxItems')
}

def _lookup_type_of(name):
    for t, names in _PROPS_TYPE_LOOKUP.items():
        if name in names:
            return t
    return str

def _process_path(fsm_obj, **kwargs):
    lines = fsm_obj._buffer.splitlines()
    cleaned_lines = _clean_lines(lines)
    for i, line in enumerate(cleaned_lines, start=1):
        matcher = re.match(QUERYSPEC_REGEX, line, re.IGNORECASE)
        param = Param(name=matcher.group('name'),
                      dtype=matcher.group('type') or 'string',
                      ptype="path",
                      description=str(matcher.group(
                            'description')).strip(),
                      required=True,
                      order=i
                      )
        fsm_obj.spec.path_params[param.name] = param
    fsm_obj._buffer = ""

def _get_real_value(name, value):
    dtype = _lookup_type_of(name)
    return dtype(value)


def _get_description_props(description:str):
    """Returns description, kwargs"""
    kwargs = {}

    index = description.rfind(':')
    while index > -1:
        description, value = description[0:index], description[index+1:]
        boundary = max(description.rfind(' '), description.rfind('\n'))
        description, name  = description[0:boundary], description[boundary+1:]
        kwargs[name] = _get_real_value(name, value.strip())
        index = description.rfind(':')
    
    return description, kwargs



def _process_query(fsm_obj, **kwargs):
    # get buffer and conver
           # first merge lines without -- to previous lines
    lines = fsm_obj._buffer.splitlines()
    cleaned_lines = _clean_lines(lines)

    # parse the lines
    for line in cleaned_lines:
        matcher = re.match(QUERYSPEC_REGEX, line.lstrip(), re.IGNORECASE)
        param = Param(name=matcher.group('name'),
                      dtype=matcher.group('type') or 'string',
                      ptype="query",
                      required=str(matcher.group('required')
                                   ).lower() == "required",
                      )
        description=str(matcher.group('description')).strip()
        desc, kwargs = _get_description_props(description)
        param.description = desc.strip()
        param.kwargs = kwargs
        fsm_obj.spec.query_params[param.name] = param
    fsm_obj._buffer = ""


def _process_body(fsm_obj, **kwargs):
    # first merge lines without -- to previous lines
    lines = fsm_obj._buffer.splitlines()
    cleaned_lines = _clean_lines(lines)
    if cleaned_lines:
        line = cleaned_lines[0]  # get the first one only
        matcher = re.match(QUERYSPEC_REGEX, line, re.IGNORECASE)
        param = Param(name=matcher.group('name'),
                      dtype=matcher.group('type') or 'string',
                      ptype="body",
                      required=not (
                            str(matcher.group('required')).lower() == "optional"),
                      )
        description=str(matcher.group('description')).strip()
        desc, kwargs = _get_description_props(description)
        param.description = desc.strip()
        param.kwargs = kwargs
        fsm_obj.spec.body_param = param
    fsm_obj._buffer = ""


def _process_cookie(fsm_obj, **kwargs):
    lines = fsm_obj._buffer.splitlines()
    cleaned_lines = _clean_lines(lines)

    for line in cleaned_lines:
        matcher = PARAM_MATCHER.match(line)
        if matcher:
            param = Param(name=matcher.group('name'),
                          dtype=matcher.group('type') or 'string',
                          ptype="cookie",
                          required=str(matcher.group('required')
                                       ).lower() == "required",
                          )
            description=str(matcher.group('description')).strip()
            desc, kwargs = _get_description_props(description)
            param.description = desc.strip()
            param.kwargs = kwargs
            fsm_obj.spec.cookie_params[param.name] = param
    fsm_obj._buffer = ""


def _process_header(fsm_obj):
    lines = fsm_obj._buffer.splitlines()
    cleaned_lines = _clean_lines(lines)

    # parse the lines
    for line in cleaned_lines:
        matcher = re.match(QUERYSPEC_REGEX, line, re.IGNORECASE)
        param = Param(name=matcher.group('name'),
                      dtype=matcher.group('type') or 'string',
                      ptype="header",
                      required=str(matcher.group('required')
                                   ).lower() == "required",
                      )
        description=str(matcher.group('description')).strip()
        desc, kwargs = _get_description_props(description)
        param.description = desc.strip()
        param.kwargs = kwargs
        fsm_obj.spec.header_params[param.name] = param


def _process_response(fsm_obj, **kwargs):
    lines = fsm_obj._buffer.splitlines()
    cleaned_lines = _clean_lines(lines)
    cur_code = kwargs.get('code', '200')
    for line in cleaned_lines:
        matcher = PARAM_MATCHER.match(line)
        if matcher:
            param = Param(name=cur_code,
                          dtype=matcher.group('type') or 'string',
                          ptype='response',
                          description=str(matcher.group(
                              'description')).strip()
                          )
            description=str(matcher.group('description')).strip()
            desc, kwargs = _get_description_props(description)
            param.description = desc.strip()
            param.kwargs = kwargs
            fsm_obj.spec.responses[cur_code] = param
    fsm_obj._buffer = ""


def _process_properties(fsm_obj, **kwargs):
    lines = fsm_obj._buffer.splitlines()
    cleaned_lines = _clean_lines(lines)

    for line in cleaned_lines:
        matcher = PARAM_MATCHER.match(line)
        if matcher:
            param = Param(name=matcher.group('name'),
                          dtype=matcher.group('type') or 'string',
                          ptype='property',
                          required=str(matcher.group('required')
                                       ).lower() == "required",
                          )
            description=str(matcher.group('description')).strip()
            desc, kwargs = _get_description_props(description)
            param.description = desc.strip()
            param.kwargs = kwargs
            fsm_obj.spec.properties[param.name] = param
    fsm_obj._buffer = ""


def _process_errors(fsm_obj, **kwargs):
    lines = fsm_obj._buffer.splitlines()
    cleaned_lines = _clean_lines(lines)

    for line in cleaned_lines:
        matcher = ERRORSPEC_MATCHER.match(line)
        if matcher:
            param = Param(name=matcher.group('code'), dtype=None,
                          description=matcher.group('description'), ptype='response')
            fsm_obj.spec.responses[matcher.group('code')] = param

    fsm_obj._buffer = ""


def _clean_lines(lines: []):
    cleaned_lines, lines = [lines[0].strip()], lines[1:]
    while lines:
        cur_line, lines = lines[0], lines[1:]
        try:
            index = cur_line.lstrip().index(' -- ') 
            cleaned_lines.append(cur_line.strip())
        except ValueError:
            cleaned_lines[-1] = cleaned_lines[-1] + " " + cur_line.strip()
    return cleaned_lines
