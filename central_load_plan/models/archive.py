import os
import re

class FolderArchive:

    def __init__(self, dir_format_string, parser=None, use_cache=True):
        self.dir_format_string = dir_format_string
        self.parser = parser
        self.use_cache = use_cache
        self._cache = {} # path resolved with subs -> full paths

    def resolve_path(self, subs):
        return self.dir_format_string.format(**subs)

    def iter_files(self, subs):
        path = self.resolve_path(subs)

        if self.use_cache and path in self._cache:
            # Generate cached files
            yield from iter(self._cache[path])
            return

        # Collect paths and data from filesystem.
        rows = []
        try:
            for fn in os.listdir(path):
                fnpath = os.path.join(path, fn)
                data = {'path': fnpath}
                if self.parser:
                    data = self.parser(fnpath)
                    data['path'] = fnpath
                rows.append(data)
            yield from iter(rows)
        except FileNotFoundError:
            pass

        if self.use_cache:
            # Save paths to cache.
            self._cache[path] = rows


class StringParser:

    def __init__(self, regex, schema=None, raise_for_match=False):
        self.regex = re.compile(regex)
        self.schema = schema
        self.raise_for_match = raise_for_match

    def __call__(self, string):
        match = self.regex.match(string)
        if self.raise_for_match and not match:
            raise ValueError(f'No match for {string}')
        data = match.groupdict()
        if self.schema:
            # Apply schema to strings
            data = self.schema.load(data)
        return data
