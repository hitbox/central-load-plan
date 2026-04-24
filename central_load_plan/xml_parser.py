import xml.etree.ElementTree as ET

class Parser:

    @classmethod
    def fields(cls):
        for name in dir(cls):
            attr = getattr(cls, name)
            if isinstance(attr, XMLField):
                yield attr

    @classmethod
    def parse_path(cls, path):
        tree = ET.parse(path)
        root = tree.getroot()
        data = {}
        for field in cls.fields():
            data[field.name] = field.extract(root)
        return data


class XMLField:

    def __init__(
        self,
        xpath,
        name = None,
        attr = None,
        default = None,
        cast = str,
        multiple = False,
        namespaces = None,
        raise_for_exists = True,
        subfield = None,
    ):
        self.name = name
        self.xpath = xpath
        self.attr = attr
        self.default = default
        self.cast = cast
        self.multiple = multiple
        if namespaces is None:
            namespaces = {}
        self.namespaces = namespaces
        self.raise_for_exists = raise_for_exists
        self.subfield = subfield

    def __set_name__(self, owner, name):
        self.name = name

    def extract(self, root):
        elems = root.findall(self.xpath, self.namespaces)

        if not elems:
            if self.raise_for_exists:
                raise ValueError(f'No elements found for name={self.name} {self.xpath}')
            return self.default

        def extract_one(el):
            # delegate if subfield exists
            if self.subfield:
                return self.subfield.extract(el)

            if self.attr:
                val = el.attrib[self.attr]
            else:
                val = el.text
            if val is None:
                return self.default
            return self.cast(val)

        results = [extract_one(el) for el in elems if extract_one(el) is not None]

        if not self.multiple and len(results) > 1:
            tags = [el.tag for el in elems]
            raise ValueError(
                f'Multiple elements {tags=} found for single field name={self.name}'
            )

        return results[0] if results else self.default
