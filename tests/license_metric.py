import unittest
from metrics.license import *  # pyright: ignore[reportWildcardImportFromLibrary]
from pathlib import Path
import os, shutil


class LicenseMetricTest(unittest.TestCase):
    TEST_DIR = Path("tests/license_tests")
    in_readme_dir = TEST_DIR / "typical_model"
    linked_license_dir = TEST_DIR / "typical_proprietary_model"
    linked_license_md_dir = TEST_DIR / "typical_proprietary_model_2"
    no_readme_dir = TEST_DIR / "extremely_weird_model"
    text_in_readme_dir = TEST_DIR / "theoretically_possible_model"
    no_license_dir = TEST_DIR / "fake_model"
    mit_license = Path("sample_licenses/MIT.txt")
    lgpl_v3_license = Path("sample_licenses/lgpl v3.txt")

    def setUp(self) -> None:
        # set up testing directories
        if self.TEST_DIR.exists():
            shutil.rmtree(self.TEST_DIR)
        os.mkdir(self.TEST_DIR)
        os.mkdir(self.in_readme_dir)
        os.mkdir(self.linked_license_dir)
        os.mkdir(self.no_readme_dir)
        os.mkdir(self.text_in_readme_dir)
        os.mkdir(self.no_license_dir)

        # license included in metadata
        readme_file = self.in_readme_dir / "README.md"
        with open(readme_file, "wt") as file:
            file.writelines(
                [
                    "---",
                    "license: lgpl-2.1",
                    "---",
                    "# Typical Model",
                    "This is a normal model :)",
                ]
            )

        # license included as a link to a LICENSE file
        readme_file = self.linked_license_dir / "README.md"
        with open(readme_file, "wt") as file:
            file.writelines(
                [
                    "---",
                    "license: other",
                    "license-name: idk" "---",
                    "# Proprietary Model",
                    "This is a big model with weird permission :/",
                    "# License",
                    "Lol no actually it's just [LGPL v3](LICENSE)",
                ]
            )
        shutil.copy(self.lgpl_v3_license, self.linked_license_dir / "LICENSE")

        # license included as a link to a LICENSE.md file
        readme_file = self.linked_license_md_dir / "README.md"
        with open(readme_file, "wt") as file:
            file.writelines(
                [
                    "---",
                    "license: other",
                    "license-name: idk" "---",
                    "# Proprietary Model",
                    "This is a big model with weird permission :/",
                    "# License",
                    "Lol no actually it's just [MIT](LICENSE.md)",
                ]
            )
        shutil.copy(self.mit_license, self.linked_license_md_dir / "LICENSE.md")

        # license included as LICENSE but no readme present
        readme_file = self.no_readme_dir / "README.md"
        shutil.copy(self.mit_license, self.no_readme_dir / "LICENSE.md")

        # license text included in full in the readme
        mit_text: list[str]
        with open(self.mit_license, "rt") as file:
            mit_text = file.readlines()
        readme_file = self.text_in_readme_dir / "README.md"
        with open(readme_file, "wt") as file:
            file.writelines(
                [
                    "---",
                    "license: other",
                    "license-name: idk" "---",
                    "# Proprietary Model",
                    "Collect my pages.",
                    "# License",
                    "",
                ]
            )
            file.writelines(mit_text)
            file.writelines(
                [
                    "# Credits",
                    "ChatGPT made this entire thing, which is why I can't use a more restrictive license.",
                    "I don't know if I technically own this code, honestly?",
                ]
            )

        # no license
        with open(self.no_license_dir / "todo.txt", "wt") as file:
            file.write("TODO: create model")

        return super().setUp()
    
    def tearDown(self) -> None:
        shutil.rmtree(self.TEST_DIR)
        return super().tearDown()
