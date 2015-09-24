import json
import logging
import requests
from functools import partial

from discover import discover

logger = logging.getLogger('photoboot.client')
HEADERS = {'content-type': 'application/json'}
CAMERA = 'camera'

_l = logging.getLogger('photoboot')
_l.setLevel(logging.DEBUG)
_l.addHandler(logging.StreamHandler())


class APICallError(Exception):

	def __init__(self, method, params, version, error_code, error_text):
		logger.error("Calling %s(%s, version=%s) resulted in this error: (%s) %s", method, params, version, error_code,
						error_text)
		self.method = method
		self.params = params
		self.version = version
		self.error_code = error_code
		self.error_text = error_text

	def __repr__(self):
		return "Calling {s.method}({s.params}, version={s.version}) " \
		       "resulted in this error: ({s.error_code}) {s.error_text}".format(s=self)


class Camera(object):

	def __init__(self, source_ip=None):
		self.services = discover(source_ip)
		self.max_version = sorted(self.request('getVersions')['result'])[0][-1]
		self.methods_info = {}
		methods = self.request('getMethodTypes', params=(self.max_version, ))['results']
		for m in methods:
			api_name, request_parameters, response_parameters, api_version = m
			self.methods_info[api_name] = {
				'request': request_parameters,
				'response': response_parameters,
				'api_version': api_version
			}

	def api_call(self, method, *params):
		method_info = self.methods_info[method]
		assert len(params) == len(method_info['request'])
		return self.request(method, version=method_info['api_version'], params=params)

	def request(self, method, version="1.0", id_=1, params=()):
		camera_url = self.services[CAMERA] + "/" + CAMERA

		# Example echo method
		payload = {
			"method": method,
			"params": params,
			"version": version,
			"id": id_,
		}
		logger.info("%s?method=%s, params=%s, version=%s", camera_url, method, params, version)
		result = requests.post(camera_url, data=json.dumps(payload), headers=HEADERS)
		data = result.json()
		if 'error' in data:
			error_code, error_text = data['error']
			raise APICallError(method, params, version, error_code, error_text)
		logger.debug(data)
		return data

	def __getattr__(self, item):
		if item not in self.methods_info:
			raise AttributeError('Method {} is not available'.format(item))
		return partial(self.api_call, item)


def main():
	c = Camera()
	while True:
		raw_cmd = raw_input("camera > ").split(" ")
		method = raw_cmd[0]
		params = raw_cmd[1:]
		if not method:
			continue
		try:
			getattr(c, method)(*params)
		except (AttributeError, APICallError) as exc:
			print exc


if __name__ == "__main__":
	main()
