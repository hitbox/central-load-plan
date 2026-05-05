"""
Declarative style XML parsing.
"""
import xml.etree.ElementTree as ET

class Parser:
    """
    Main XML Parser class.
    """

    @classmethod
    def fields(cls):
        """
        Generate the declarative xml fields defined on a subclass.
        """
        for name in dir(cls):
            attr = getattr(cls, name)
            if isinstance(attr, XMLField):
                yield attr

    @classmethod
    def parse_path(cls, path):
        """
        Parse and return the data from an XML file.
        """
        tree = ET.parse(path)
        root = tree.getroot()
        data = {}
        for field in cls.fields():
            data[field.name] = field.extract(root)
        return data


class XMLField:
    """
    A declarative XML field class. Uses xpath from some root element to find
    data from an attribute or just the text of the element.
    """

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
        """
        :param xpath: An xpath string to find elment(s) relative to some other
        element.
        :param name: Name to use for key in data dictionary. Usually taken from
        the name an instance of this class is assigned to. Argument form mainly
        for subfield.
        :param attr: If not None, name of attribute of xpath element to take as
        the value when parsing.
        :param default: Default value to return for parsing.
        :param cast: Callable to finalize value for returning.
        :param multiple: Flag to allow many values returned in a list.
        :param namespaces: Dictionary to use when searching with xpath.
        :param raise_for_exists: Flag to raise error if element is not found.
        :param subfield: If not None, should be an object with .extract method
        to defer to for getting final value to return. Used to nest data
        structures.
        """
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
        """
        Get the name for this instance from assignment.
        """
        self.name = name

    def extract(self, root):
        """
        Extract text or attribute from xpath element found, relative to `root`.
        """
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
    """
    Exists to make XMLField `.extract` behave like Parser.parse_path and simply
    return a dictionary of the extracted data. Instead of trying to delegate to
    subfield.
    """

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
