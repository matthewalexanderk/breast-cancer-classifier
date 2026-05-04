import ast
import unittest

import python_learning_game as game


class RequirementTests(unittest.TestCase):
    def _check(self, requirement: game.Requirement, code: str) -> bool:
        tree = ast.parse(code, mode="exec")
        return requirement.check(tree)

    def test_requires_class_structure_passes_for_init_and_method(self) -> None:
        requirement = game.requires_class_structure("message", "name")
        code = (
            "class Bot:\n"
            "    def __init__(self):\n"
            "        self.steps = []\n"
            "    def run(self):\n"
            "        return self.steps\n"
        )
        self.assertTrue(self._check(requirement, code))

    def test_requires_class_structure_rejects_missing_method(self) -> None:
        requirement = game.requires_class_structure("message", "name")
        code = (
            "class Bot:\n"
            "    def __init__(self):\n"
            "        self.steps = []\n"
        )
        self.assertFalse(self._check(requirement, code))

    def test_requires_self_attribute_usage(self) -> None:
        requirement = game.requires_self_attribute_usage("message", "name")
        self.assertTrue(
            self._check(
                requirement,
                "class Bot:\n"
                "    def __init__(self):\n"
                "        self.steps = []\n",
            )
        )
        self.assertFalse(
            self._check(
                requirement,
                "class Bot:\n"
                "    def __init__(self):\n"
                "        steps = []\n",
            )
        )

    def test_requires_class_instantiation(self) -> None:
        requirement = game.requires_class_instantiation("message", "name")
        self.assertTrue(
            self._check(
                requirement,
                "class Bot:\n"
                "    def __init__(self):\n"
                "        self.steps = []\n"
                "\n"
                "bot = Bot()\n",
            )
        )
        self.assertFalse(
            self._check(
                requirement,
                "class Bot:\n"
                "    def __init__(self):\n"
                "        self.steps = []\n",
            )
        )


if __name__ == "__main__":
    unittest.main()
