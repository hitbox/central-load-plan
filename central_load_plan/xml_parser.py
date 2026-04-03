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

    def __set_name__(self, owner, name):
        self.name = name

    def extract(self, root):
        if self.multiple:
            elems = root.findall(self.xpath, self.namespaces)
            if self.raise_for_exists and not elems:
                raise ValueError(f'No elements found for name={self.name} {self.xpath} on {root=}')
            values = []
            for el in elems:
                val = el.attrib[self.attr] if self.attr else el.text
                if val is not None:
                    values.append(self.cast(val))
            return values or self.default
        else:
            el = root.find(self.xpath, self.namespaces)
            if self.raise_for_exists and el is None:
                raise ValueError(f'name={self.name} Not found {self.xpath} on {root=}')
            if el is None:
                return self.default
            val = el.attrib[self.attr] if self.attr else el.text
            if val is None:
                val = self.default
            else:
                val = self.cast(val)
            return val


class NestedXMLField(XMLField):

    def __init__(self, xpath, subfield, name=None, attr=None, default=None, cast=str, multiple=False, namespaces=None, raise_for_exists=True):
        super().__init__(
            xpath = xpath,
            name = name,
            attr = attr,
            default = default,
            cast = cast,
            multiple = multiple, # ignored
            namespaces = namespaces,
            raise_for_exists = raise_for_exists,
        )
        self.subfield = subfield

    def extract(self, elem):
        list_ = []
        for elem in elem.findall(self.xpath, self.namespaces):
            list_.append(self.subfield.extract(elem))
        return list_
