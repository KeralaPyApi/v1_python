import json
import re
from pathlib import Path

API_PATH = Path('api')
TEMPLATE = Path('gotgrambot/template')
RESULTS = Path("gotgrambot")

TG_CORE_TYPES = {
    "String": 'string',
    "Boolean": 'bool',
    "Integer": 'int64',
    "Float": 'float64'
}

CORE_TYPES = ['int64', 'float64', 'bool', 'string']

subclass_temp = """func (v {class_name}) Get{method}() {class_name} {{
    return v
}}

"""

TYPE_CONTENT = ''
METHOD_CONTENT = ''


def snake(s: str):
    # https://stackoverflow.com/q/1175208
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def camel(s: str):
    return "".join([i[0].upper() + i[1:] for i in s.split("_")])


def build_types(content):
    with open(API_PATH / 'api.json') as f:
        content_temp = open(TEMPLATE / 'content.tmpl', mode='r').read()
        type_temp = open(TEMPLATE / 'common.tmpl', mode='r').read()
        schema = json.loads(f.read()).get('types')
        subclass_dict = {}
        for name, item in schema.items():
            subclasses = item.get('subtypes')
            comments = "// " + "\n// ".join(item.get('description'))
            fields = item.get('fields')
            if subclasses and len(subclasses) != 0:
                field_text = get_inheritance(subclasses, subclass_dict, schema, name)
                content += content_temp.format(
                    name=name,
                    mode="struct",
                    comments=comments,
                    fields=field_text[:-1]
                )

            elif fields is None:
                content += content_temp.format(
                    name=name,
                    mode="struct",
                    comments=comments,
                    fields=""
                )
            else:
                field_text = ''
                for field in fields:
                    text = ''
                    for types in field.get('types'):
                        field_name = field.get('name')

                        def_types = get_type(types)
                        if "InputFile" in def_types:
                            continue
                        if field_name == "chat_id" and def_types == "string":
                            continue
                        text += get_field_text(field_name, def_types, field)
                    field_text += text

                content += content_temp.format(
                    name=name,
                    mode="struct",
                    comments=comments,
                    fields=field_text[:-1]
                )

                if subclass_dict.get(name):
                    method = subclass_dict.get(name)
                    content += subclass_temp.format(
                        class_name=name,
                        method=method
                    )

        with open(RESULTS / "types.go", "w+", encoding="utf-8") as type_file:
            type_file.write(
                type_temp.format(
                    content=content
                )
            )


def get_type(types):
    def_types = TG_CORE_TYPES.get(types) if TG_CORE_TYPES.get(types) is not None else types
    if def_types.startswith("Array of Array"):
        def_types = f"[][]{TG_CORE_TYPES.get(f'{def_types[18:]}')}" if TG_CORE_TYPES.get(
            f'{def_types[18:]}') is not None else f'*[][]{def_types[18:]}'
    elif def_types.startswith("Array of"):
        def_types = f"[]{TG_CORE_TYPES.get(f'{def_types[9:]}')}" if TG_CORE_TYPES.get(
            f'{def_types[9:]}') is not None else f'*[]{def_types[9:]}'
    else:
        def_types = def_types if def_types in CORE_TYPES else f'*{def_types}'
    return def_types


def get_field_text(field_name, def_types, field, comments=True):
    if field.get('required'):
        empty = ""
    else:
        empty = ",omitempty"
    if comments:
        text = f'    // {field.get("description")}\n'\
            f'    {camel(field_name)} {def_types} `json:"{field_name}{empty}"`\n'
    else:
        text = f'    {camel(field_name)} {def_types} `json:"{field_name}{empty}"`\n'
    return text


def get_inheritance(subclasses, subclass_dict, schema, name):
    field_text = ''
    sub_fields_list = []
    for subclass in subclasses:
        subclass_dict.update({subclass: name})
        sub_schema = schema.get(subclass)
        text = ''
        for sub_fields in sub_schema.get('fields'):
            sub_field_name = sub_fields.get('name')
            if sub_field_name in sub_fields_list:
                continue
            else:
                sub_fields_list.append(sub_field_name)
                for sub_types in sub_fields.get('types'):
                    sub_def_types = get_type(sub_types)
                    if "InputFile" in sub_def_types:
                        continue
                    if sub_field_name == "chat_id" and sub_def_types == "string":
                        continue

                    text += get_field_text(sub_field_name, sub_def_types, sub_fields, comments=False)
        field_text += text
    return field_text


if __name__ == '__main__':
    build_types(TYPE_CONTENT)
