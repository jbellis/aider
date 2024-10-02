import unittest
from unittest.mock import MagicMock, patch

from aider.models import Model, get_model_info, sanity_check_model


class TestModels(unittest.TestCase):
    def test_get_model_info_nonexistent(self):
        info = get_model_info("non-existent-model")
        self.assertEqual(info, {})

    def test_max_context_tokens(self):
        model = Model("gpt-3.5-turbo")
        self.assertEqual(model.info["max_input_tokens"], 16385)

        model = Model("gpt-3.5-turbo-16k")
        self.assertEqual(model.info["max_input_tokens"], 16385)

        model = Model("gpt-3.5-turbo-1106")
        self.assertEqual(model.info["max_input_tokens"], 16385)

        model = Model("gpt-4")
        self.assertEqual(model.info["max_input_tokens"], 8 * 1024)

        model = Model("gpt-4-32k")
        self.assertEqual(model.info["max_input_tokens"], 32 * 1024)

        model = Model("gpt-4-0613")
        self.assertEqual(model.info["max_input_tokens"], 8 * 1024)

    @patch("os.environ")
    def test_sanity_check_model_all_set(self, mock_environ):
        mock_environ.get.return_value = "dummy_value"
        mock_io = MagicMock()
        model = MagicMock()
        model.name = "test-model"
        model.missing_keys = ["API_KEY1", "API_KEY2"]
        model.keys_in_environment = True
        model.info = {"some": "info"}

        sanity_check_model(mock_io, model)

        mock_io.tool_output.assert_called()
        calls = mock_io.tool_output.call_args_list
        self.assertIn("- API_KEY1: Set", str(calls))
        self.assertIn("- API_KEY2: Set", str(calls))

    @patch("os.environ")
    def test_sanity_check_model_not_set(self, mock_environ):
        mock_environ.get.return_value = ""
        mock_io = MagicMock()
        model = MagicMock()
        model.name = "test-model"
        model.missing_keys = ["API_KEY1", "API_KEY2"]
        model.keys_in_environment = True
        model.info = {"some": "info"}

        sanity_check_model(mock_io, model)

        mock_io.tool_output.assert_called()
        calls = mock_io.tool_output.call_args_list
        self.assertIn("- API_KEY1: Not set", str(calls))
        self.assertIn("- API_KEY2: Not set", str(calls))

    @patch("aider.models.sanity_check_model")
    def test_sanity_check_models_bogus_editor(self, mock_sanity_check_model):
        mock_io = MagicMock()
        main_model = MagicMock()
        main_model.name = "gpt-4"
        main_model.weak_model = None
        main_model.editor_model = MagicMock()
        main_model.editor_model.name = "bogus-model"

        # Set up mock to return False for main model and True (problem) for editor model
        mock_sanity_check_model.side_effect = [False, True]

        result = sanity_check_models(mock_io, main_model)

        self.assertTrue(
            result
        )  # Should return True because there's a problem with the editor model
        mock_sanity_check_model.assert_called_with(mock_io, main_model.editor_model)
        mock_io.tool_warning.assert_called_once()  # Ensure a warning was issued


if __name__ == "__main__":
    unittest.main()
