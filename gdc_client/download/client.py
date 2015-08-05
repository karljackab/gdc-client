import requests

from parcel import HTTPClient, UDTClient
from parcel.download_stream import DownloadStream
from ..log import get_logger
from ..query.index import GDCIndexClient

# Logging
log = get_logger('client')


class GDCDownloadMixin(object):

    def download_related_files(self, index, file_id, directory):
        """Finds and downloads files related to the primary entity.

        :param str file_id: String containing the id of the primary entity
        :param str directory: The primary entity's directory

        """

        for related_file in index.get_related_files(file_id):
            stream = DownloadStream(related_file, self.uri, directory)
            self._download(self.n_procs, stream)

    def download_annotations(self, index, file_id, directory):
        """Finds and downloads annotations related to the primary entity.

        :param str file_id: String containing the id of the primary entity
        :param str directory: The primary entity's directory

        """

        annotations = index.get_annotations(file_id)
        log.info('Annotations for {}: {}'.format(file_id, annotations))

        if annotations:
            annotation_list = ','.join(annotations)
            stream = DownloadStream(annotation_list, self.uri, directory)
            self.serial_download(stream)

    def parallel_download(self, stream, download_related_files=None,
                          download_annotations=None, *args, **kwargs):

        # Download primary file
        super(GDCDownloadMixin, self).parallel_download(
            stream, *args, **kwargs)

        # Create reference to GDC Query API
        index = GDCIndexClient(self.base_uri)

        # Recurse on related files
        if download_related_files or\
           download_related_files is None and self.related_files:
            try:
                self.download_related_files(index, stream.ID, stream.directory)
            except Exception as e:
                log.warn('Unable to download related files for {}: {}'.format(
                    stream.ID, e))
                if self.debug:
                    raise

        # Recurse on annotations
        if download_annotations or\
           download_annotations is None and self.annotations:
            try:
                self.download_annotations(index, stream.ID, stream.directory)
            except Exception as e:
                log.warn('Unable to download annotations for {}: {}'.format(
                    stream.ID, e))
                if self.debug:
                    raise


class GDCHTTPDownloadClient(GDCDownloadMixin, HTTPClient):

    def __init__(self, uri, download_related_files=True,
                 download_annotations=True, *args, **kwargs):
        self.base_uri = uri
        self.data_uri = uri + 'data'
        self.related_files = download_related_files
        self.annotations = download_annotations
        super(GDCDownloadMixin, self).__init__(self.data_uri, *args, **kwargs)


class GDCUDTDownloadClient(GDCDownloadMixin, UDTClient):

    def __init__(self, remote_uri, download_related_files=True,
                 download_annotations=True, *args, **kwargs):

        remote_uri = self.fix_uri(remote_uri)
        self.base_uri = remote_uri
        self.data_uri = remote_uri + 'data'
        self.related_files = download_related_files
        self.annotations = download_annotations

        super(GDCDownloadMixin, self).__init__(
            remote_uri=self.data_uri, *args, **kwargs)
