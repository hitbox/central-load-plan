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
        xpath = '.',
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
        # subfield has .extract method and it's result is lifted up as our result.
        self.subfield = subfield

    def __set_name__(self, owner, name):
        self.name = name

    def extract(self, root):
        elems = root.findall(self.xpath, self.namespaces)

        if not elems and self.raise_for_exists:
            raise ValueError(
                f'No elements found for name={self.name} {self.xpath}')

        def extract_one(el):
            # delegate if subfield exists
            if self.subfield:
                val = self.subfield.extract(el)
                return val

            if self.attr:
                val = el.attrib[self.attr]
            else:
                val = el.text
            if val is None:
                return self.get_default_value()
            return self.cast(val)

        results = []
        for el in elems:
            val = extract_one(el)
            if val is not None:
                results.append(val)

        if not self.multiple and len(results) > 1:
            tags = [el.tag for el in elems]
            name = self.name
            raise ValueError(
                f'Multiple elements {tags=} found for {name=}'
            )

        if results:
            if not self.multiple:
                return results[0]
            else:
                return results
        else:
            return self.get_default_value()

    def get_default_value(self):
        default = self.default
        if callable(default):
            default = default()
        return default


class NestedXMLField(XMLField):

    def extract(self, root):
        elems = root.findall(self.xpath, self.namespaces)

        # raise if configured for must exist
        if not elems:
            if not self.raise_for_exists:
                return self.get_default_value()
            else:
                raise ValueError(
                    f'No elements found for {self.name!r}')

        def extract_one(el):
            result = {}
            for name in dir(type(self)):
                field = getattr(type(self), name)
                if isinstance(field, XMLField):
                    result[field.name] = field.extract(el)
            return result

        results = [extract_one(el) for el in elems]
        if not self.multiple:
            return results[0]
        else:
            return results
