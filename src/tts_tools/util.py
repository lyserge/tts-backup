import json
import zipfile
import os
import time
import pkg_resources


REVISION = pkg_resources.require("tts-backup")[0].version


class ShadowProxy:
    """Proxy objects for arbitrary objects, with the ability to divert
    attribute access from one attribute to another.

    """

    def __init__(self, proxy_for):
        self.__target = proxy_for
        self.__diverted = {}

    def divert_access(self, source, target):
        self.__diverted[source] = target

    def __getattr__(self, name):
        if name in self.__diverted:
            name = self.__diverted[name]
        return getattr(self.__target, name)


class ZipFile (zipfile.ZipFile):
    """A ZipFile that supports dry-runs.

    It also keeps track of files already written, and only writes them
    once. ZipFile.filelist would have been useful for this, but on
    Windows, this doesn’t seem to reflect writes before syncing the
    file to disk.
    """

    def __init__(self,
                 file,
                 mode='r',
                 *args,
                 dry_run=False,
                 ignore_missing=False,
                 rewrite=False,
                 **kwargs):

        self.dry_run = dry_run
        self.stored_files = set()
        self.ignore_missing = ignore_missing
        self.rewrite = rewrite

        if mode=='r' or not self.dry_run:
            super().__init__(file, mode, *args, **kwargs)

    def __exit__(self, *args, **kwargs):

        if not self.dry_run:
            super().__exit__(*args, **kwargs)

    def write(self, filename, *args, **kwargs):

        if filename in self.stored_files:
            return

        # Logging.
        curdir = os.getcwd()
        absname = os.path.join(curdir, filename)
        log_skipped = lambda: print("{} (not found)".format(absname))
        log_written = lambda: print(absname)

        if not (os.path.isfile(filename) or self.ignore_missing):
            raise FileNotFoundError("No such file: {}".format(filename))

        if self.dry_run and os.path.isfile(filename):
            log_written()

        elif self.dry_run:
            log_skipped()

        else:
            try:
                super().write(filename, *args, **kwargs)
            except FileNotFoundError:
                assert self.ignore_missing
                log_skipped()
            else:
                log_written()

        self.stored_files.add(filename)

    def extract(self, member, path, *args, **kwargs):
        absname = os.path.join(path, member.filename)
        log_skipped = lambda: print("{} (already exists)".format(absname))
        log_write_error = lambda: print("{} (could not write)".format(absname))
        log_written = lambda: print(absname)

        if (os.path.isfile(absname) and not self.rewrite):
            log_skipped()
            print('skipping because file already exists')
        else:
            try:
                if not self.dry_run:
                    super().extract(member, path, *args, **kwargs)
            except:
                log_write_error()
                raise
            else:
                log_written()


    def put_metadata(self, comment=None, info_filename=None):
        """Create a MANIFEST file and store it within the archive."""

        manifest = dict(script_revision=REVISION,
                        export_date=round(time.time()))

        if comment:
            manifest['comment'] = comment
        if info_filename:
            manifest['info_filename'] = info_filename

        manifest = json.dumps(manifest)
        self.comment = manifest.encode('utf-8')


    def get_metadata(self):
        """Read metadata from the MANIFEST file in the archive."""
        return json.loads(self.comment)


def print_err(*args, **kwargs):
    # stderr could be reset at run-time, so we need to import it when
    # the function runs, not when this module is imported.
    from sys import stderr
    if 'file' in kwargs:
        del kwargs['file']
    print(*args, file=stderr, **kwargs)


def strip_mime_parms(mime_type):
    "Remove any MIME parameters from a content-type header value."
    idx = mime_type.find(";")
    has_parms = idx >= 0
    if has_parms:
        return mime_type[:idx]
    else:
        return mime_type
