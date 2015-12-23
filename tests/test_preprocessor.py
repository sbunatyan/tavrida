import unittest

import mock

from tavrida import preprocessor
from tavrida import steps


class PreprocessorTestCase(unittest.TestCase):

    def setUp(self):
        super(PreprocessorTestCase, self).setUp()
        self.router = mock.MagicMock()
        self.service_list = [mock.MagicMock()]
        self.preprocessor = preprocessor.PreProcessor(self.router,
                                                      self.service_list)

    def test_first_two_steps_in_list(self):
        """
        Tests that the first step is ValidateMessageMiddleware and the second
        is CreateMessageMiddleware
        """

        self.assertIsInstance(self.preprocessor._steps[0],
                              steps.ValidateMessageMiddleware)
        self.assertIsInstance(self.preprocessor._steps[1],
                              steps.CreateMessageMiddleware)

    def test_process_runs_middlewares_and_router(self):
        """
        Tests all steps are called and finally message is provided to router
        """

        message = mock.MagicMock()
        first_step = mock.MagicMock()
        self.preprocessor._steps = [first_step]

        self.preprocessor.process(message)
        for step in self.preprocessor._steps:
            step.process.assert_called_once_with(message)
        self.router.process.assert_called_once_with(first_step.process(),
                                                    self.service_list)
