import unittest

from tavrida import entry_point


class EntryPointFactoryTestCase(unittest.TestCase):

    def setUp(self):
        super(EntryPointFactoryTestCase, self).setUp()
        self.ep_factory = entry_point.EntryPointFactory()

    def test_create_null(self):
        ep_string = ""
        res = self.ep_factory.create(ep_string)
        self.assertIsInstance(res, entry_point.NullEntryPoint)

    def test_create_entry_point(self):
        ep_string = "service.method"
        res = self.ep_factory.create(ep_string)
        self.assertIsInstance(res, entry_point.EntryPoint)
        self.assertEqual(res.service, "service")
        self.assertEqual(res.method, "method")

    def test_create_source(self):
        ep_string = "service.method"
        res = self.ep_factory.create(ep_string, source=True)
        self.assertIsInstance(res, entry_point.Source)
        self.assertEqual(res.service, "service")
        self.assertEqual(res.method, "method")

    def test_create_destination(self):
        ep_string = "service.method"
        res = self.ep_factory.create(ep_string, destination=True)
        self.assertIsInstance(res, entry_point.Destination)
        self.assertEqual(res.service, "service")
        self.assertEqual(res.method, "method")

    def test_create_service(self):
        ep_string = "service"
        res = self.ep_factory.create(ep_string, destination=True)
        self.assertIsInstance(res, entry_point.ServiceEntryPoint)
        self.assertEqual(res.service, "service")
        self.assertIsNone(res.method)


class NullEntryPointTestCase(unittest.TestCase):

    def setUp(self):
        super(NullEntryPointTestCase, self).setUp()
        self.null_ep = entry_point.NullEntryPoint()

    def test_str(self):
        self.assertEqual(str(self.null_ep), "")

    def test_is_false(self):
        self.assertFalse(self.null_ep)


class TestRountingKeyTestCase(unittest.TestCase):

    def test_ep_routing_key(self):
        service_name = "some_service"
        method_name = "some_method"
        rk = "some_service.some_method"
        ep = entry_point.EntryPoint(service_name, method_name)
        self.assertEqual(ep.to_routing_key(), rk)

    def test_service_routing_key(self):
        service_name = "some_service"
        rk = "some_service"
        ep = entry_point.ServiceEntryPoint(service_name)
        self.assertEqual(ep.to_routing_key(), rk)
