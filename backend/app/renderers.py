import json

from rest_framework.renderers import JSONRenderer


class DataWrappingJSONRenderer(JSONRenderer):
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is not None:
            data = data if 'pagination' in data else {'data': data}
            return json.dumps(data, indent=4)
