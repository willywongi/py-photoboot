import ssdp
import sys
import requests
from xml.etree import ElementTree
import logging

XML_SERVICE_ACTION_URL = "{urn:schemas-sony-com:av}X_ScalarWebAPI_ActionList_URL"
XML_SERVICE_TYPE_TAG = "{urn:schemas-sony-com:av}X_ScalarWebAPI_ServiceType"
XML_SERVICE_TAG = "{urn:schemas-sony-com:av}X_ScalarWebAPI_Service"
SSDP_SERVICE = "urn:schemas-sony-com:service:ScalarWebAPI:1"

logger = logging.getLogger('photoboot.discover')


def parse_capabilities_xml(file_contents):
	tree = ElementTree.fromstring(file_contents)
	services = {}
	for tag in tree.iter(XML_SERVICE_TAG):
		logger.debug('Service found: %s', tag)
		service_type = tag.find(XML_SERVICE_TYPE_TAG).text
		service_url = tag.find(XML_SERVICE_ACTION_URL).text
		services[service_type] = service_url
		logger.debug('Service info: %s/%s', service_type, service_url)
	logger.debug('Device service URLs: %s', services)
	return services


def discover(source_ip=None):
	"""
		Discover a Sony device on the network, parse its capabilities file
		and return a mapping of service/URLs
	:param source_ip: the address of the local interface to discover from
	:return: dict
	"""
	logger.info('Discovering device on network')
	res = ssdp.discover(SSDP_SERVICE, source_ip=source_ip)
	if not res:
		logger.error('No device found in network (source_ip=%s)', source_ip)
		raise IOError('No device found in network')
	device = res[0]
	logger.info('Found device %s', device)
	logger.info('Requesting its description xml file (%s)', device.location)
	r = requests.get(device.location)
	logger.info('File obtained, parsing XML')
	services = parse_capabilities_xml(r.text)
	return services


def main():
	if '-a' in sys.argv:
		source_ip = sys.argv[sys.argv.index("-a") + 1]
	else:
		source_ip = None

	if '-f' in sys.argv:
		xml_file = sys.argv[sys.argv.index("-f") + 1]
	else:
		xml_file = None

	if '-v' in sys.argv:
		logger.setLevel(logging.DEBUG)
		logger.addHandler(logging.StreamHandler())

	if xml_file:
		with open(xml_file) as handler:
			services = parse_capabilities_xml(handler.read())
	else:
		services = discover(source_ip=source_ip)
	print "Services found on network"
	for service_type, service_url in services.iteritems():
		print service_type, service_url

if __name__ == '__main__':
	main()
