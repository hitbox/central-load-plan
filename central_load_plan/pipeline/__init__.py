import glob
import inspect
import io
import os
import re
import smtplib
import uuid
import xml.etree.ElementTree as ET
import zipfile

from abc import ABC
from abc import abstractmethod
from email.message import EmailMessage
from datetime import datetime
from datetime import time

import sqlalchemy as sa

from sqlalchemy.ext.orderinglist import ordering_list
from central_load_plan import rendering
from central_load_plan.constants import APPNAME
from lxml import etree
from sqlalchemy.ext.hybrid import hybrid_property

class Base(ABC):
    """
    Base for old probably unneeded objects.
    """

class Source(Base):

    @abstractmethod
    def paths(self, substitutions=None):
        """
        Generate paths to consume.
        """


class Reader(Base):
    """
    Base reader class.
    """

    @abstractmethod
    def read(self, source):
        """
        Read xml from some source.
        """


class Output(Base):

    @abstractmethod
    def write(self, xml_data, substitutions):
        """
        Write xml_data somewhere.
        """


class Archive(Base):
    """
    Archive checks and saves if a path has been archived as processed.
    """

    @abstractmethod
    def check(self, source, xml_data):
        """
        Check if source is already processed.
        """

    @abstractmethod
    def save(self, source, xml_data):
        """
        Save path to archive.
        """


class ContextSource(Source):

    def __init__(self, context_getter, path):
        self.context_getter = context_getter
        self.path = path

    def paths(self, substitutions=None):
        if substitutions is None:
            substitutions = {}

        substitutions.update(self.context_getter())

        path = self.path.format(**substitutions)

        for fn in os.listdir(path):
            full = os.path.join(path, fn)
            yield full


class RegexParser:

    def __init__(self, regex, include_string=False):
        """
        :param regex: Named captured group regex or pattern to parse strings.
        """
        self.regex = re.compile(regex)
        self.include_string = include_string

    def __call__(self, string):
        match = self.regex.match(string)
        if match:
            data = match.groupdict()
            if self.include_string:
                if isinstance(self.include_string, str):
                    key = self.include_string
                else:
                    key = 'original'
                if key in data:
                    raise KeyError(f'{key} already exists.')
                data[key] = string
            return data
        else:
            raise ValueError(f'regex={self.regex} did not match {string=}')


class GlobSource(Source):
    """
    Generate paths from glob pattern.
    """

    def __init__(self, pathname, root_dir=None, recursive=False, include_hidden=False):
        self.pathname = pathname
        self.root_dir = root_dir
        self.recursive = recursive
        self.include_hidden = include_hidden

    def paths(self, substitutions=None):
        if substitutions is None:
            substitutions = {}
        pathname = self.pathname.format(**substitutions)

        root_dir = self.root_dir
        if root_dir is not None:
            root_dir = self.root_dir.format(**substitutions)

        kwargs = {
            'root_dir': root_dir,
            'recursive': self.recursive,
            'include_hidden': self.include_hidden,
        }

        for filename in glob.iglob(pathname, **kwargs):
            if kwargs['root_dir']:
                filename = os.path.join(kwargs['root_dir'], filename)
            filename = os.path.normpath(filename)
            yield filename


class XMLReader(Reader):
    """
    Read XML file.
    """
    # Returns the original source name for compatibility with EFFZipReader
    # which needs to report what name in the ZIP it is returning.

    def read(self, source):
        parser = etree.XMLParser(recover=True)
        tree = etree.parse(source, parser)
        root = tree.getroot()
        return (source, root)


class EFFZipReader(Reader):
    """
    Read the CLP XML file from EFF ZIP files.
    """

    xml_re = re.compile(r'[A-Z]{8}\-std\.xml$')

    def read(self, source):
        """
        Find a .dat file inside the source zip, then find the CLP xml file and
        parse it into an element tree.
        """
        # Open EFF as ZIP file (that is apparently what they really are).
        with zipfile.ZipFile(source, 'r') as eff_zip_file:
            # Find the .dat file which is another zip file inside.
            for name in eff_zip_file.namelist():
                # Check for .dat file.
                if not name.lower().endswith('.dat'):
                    continue

                # Open the .dat file as another zip.
                with eff_zip_file.open(name) as dat_zip_file_member:
                    dat_zip_bytes = io.BytesIO(dat_zip_file_member.read())
                    # Open the inner ZIP from bytes
                    with zipfile.ZipFile(dat_zip_bytes, 'r') as dat_zip_file:
                        # Find XML filename.
                        for xml_name in dat_zip_file.namelist():
                            if not self.xml_re.match(xml_name):
                                continue

                            # Open inner nested XML file.
                            with dat_zip_file.open(xml_name) as xml_file:
                                # Parse XML file inside nested ZIP file.
                                tree = ET.parse(xml_file)
                                root = tree.getroot()
                                return (xml_name, root)


class EmailOutput(Output):
    """
    Create and email report output from template.
    """
    key_pairs = (
        ('fromaddr', 'from'),
        ('toaddrs', 'to'),
        ('subject', 'subject'),
    )

    def __init__(self, smtp, fromaddr, toaddrs, subject, body_template):
        """
        :param smtp:
            Dict SMTP configuration.
        :param fromaddr:
            String email appears to come from.
        :param toaddrs:
            String to send email to.
        :param subject:
            String subject of email.
        :param body_template:
            Filename of template to render email body from.
        :param dry:
            True for dry run. Do not actually send email.
        """
        self.smtp = smtp
        self.fromaddr = fromaddr
        self.toaddrs = toaddrs
        self.subject = subject
        self.body_template = body_template
        self.logger = logging.getLogger(APPNAME)

    def _email_message(self, xml_data):
        email_message = EmailMessage()
        # Update email message from self attributes.
        for attr, key in self.key_pairs:
            email_message[key] = getattr(self, attr)
        # Add body to email message from rendered template as HTML.
        plaintext = rendering.render(self.body_template, xml_data)
        html = f'<pre>{ plaintext }</pre>'
        email_message.set_content(plaintext)
        email_message.add_alternative(html, subtype='html')
        return email_message

    def write(self, xml_data, substitutions):
        """
        Create and email message from xml data and runtime substitutions.
        """
        email_message = self._email_message(xml_data, substitutions)
        with smtplib.SMTP(**self.smtp) as smtp:
            smtp.send_message(email_message)
            self.logger.info(
                'email: %(email_message.subject)s to %(email_message.to)s',
                email_message = email_message,
            )


class NullArchive(Archive):
    """
    Do nothing archive object.
    """

    def check(self, path):
        """
        Always report path is not archived.
        """
        return False

    def save(self, path):
        """
        Do nothing with path.
        """
        return


class PathArchive(Archive):
    """
    Save path to file and avoid processing again.
    """

    def __init__(self, archive_path):
        self.archive_path = archive_path
        self._paths = set(self._load_archive())

    def _load_archive(self):
        if os.path.exists(self.archive_path):
            with open(self.archive_path, 'r') as archive_file:
                for line in archive_file:
                    yield line.strip()

    def check(self, path):
        return path in self._paths

    def save(self, path):
        self._paths.add(os.path.normpath(path))
        with open(self.archive_path, 'a') as archive_file:
            archive_file.write(path + '\n')


class MoveArchive(Archive):
    """
    Archive files by moving them.
    """

    def __init__(self, filename):
        self.filename = filename

    def check(self, path):
        """
        Assuming this path is never from where it will by moved, always report
        not archived.
        """
        return False

    def save(self, path):
        raise NotImplementedError

