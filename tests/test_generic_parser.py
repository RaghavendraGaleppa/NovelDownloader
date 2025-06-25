import unittest
import json
from pathlib import Path
from src.scraping.generic_parser import load_configs_from_directory, get_config_for_url, parse_html

MOCK_69SHU_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
<div class="txtnav">
  <h1>第123章 The Title</h1>
  <div class="txtinfo">Some info to be removed</div>
  <div id="txtright">An ad to be removed</div>
  <div class="txtnav_cont">
    This is the first paragraph of the chapter.<br>
    This is the second paragraph.
  </div>
  <div class="page1">
    <a href="/prev.htm">上一章</a>
    <a href="/book/123/457.htm">下一章</a>
  </div>
  <div class="bottom-ad">Another ad</div>
  <div class="contentadv">A content ad</div>
</div>
</body>
</html>
"""

MOCK_1QXS_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
<div class="main">
  <div class="title">
    <h1>124：Another Title</h1>
  </div>
  <div class="content">
    <p>First paragraph for 1qxs.</p>
    <p>Second paragraph.</p>
    <p>本章未完，点击</p>
    <p>Some other random text.</p>
  </div>
  <a id="next" href="/novel/45/45679.html">下一页</a>
</div>
</body>
</html>
"""

class TestGenericParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load configs once for all tests in this class."""
        cls.configs = load_configs_from_directory("scraper_configs")
        
        with open(Path("scraper_configs") / "69shu-family.json", "r", encoding="utf-8") as f:
            cls.expected_69shu_config = json.load(f)

        with open(Path("scraper_configs") / "1qxs.com.json", "r", encoding="utf-8") as f:
            cls.expected_1qxs_config = json.load(f)

    def test_load_configs_from_directory(self):
        """
        Tests that scraper configurations are loaded correctly.
        """
        # 1. Check that the returned object is a dictionary
        self.assertIsInstance(self.configs, dict)

        # 2. Check that the expected keys are present
        self.assertIn("69shu-family", self.configs)
        self.assertIn("1qxs.com", self.configs)

        # 3. Check the content of a loaded configuration
        self.assertEqual(self.configs["69shu-family"], self.expected_69shu_config)

    def test_get_config_for_url(self):
        """
        Tests that the correct config is returned for a URL.
        """
        # 1. Test direct match
        config = get_config_for_url("https://1qxs.com/some/path", self.configs)
        self.assertIsNotNone(config)
        self.assertEqual(config, self.configs["1qxs.com"])

        # 2. Test match with 'www.' subdomain (no longer a primary test case, covered by family)
        config = get_config_for_url("https://www.69shu.com/book/123.htm", self.configs)
        self.assertIsNotNone(config)
        self.assertEqual(config, self.configs["69shu-family"])
        
        # 3. Test new domain family logic
        config = get_config_for_url("https://www.69shuba.pro/book/456.htm", self.configs)
        self.assertIsNotNone(config)
        self.assertEqual(config, self.configs["69shu-family"])

        # 4. Test unsupported URL
        config = get_config_for_url("https://www.google.com", self.configs)
        self.assertIsNone(config)
        
        # 5. Test another unsupported URL
        config = get_config_for_url("https://example.org/path", self.configs)
        self.assertIsNone(config)

        # 6. Test empty/invalid URL
        config = get_config_for_url("", self.configs)
        self.assertIsNone(config)
        
        config = get_config_for_url("just-a-string", self.configs)
        self.assertIsNone(config)

    def test_parse_html_69shu(self):
        """Tests parsing logic for a 69shu.com-like page."""
        url = "https://www.some69shudomain.com/book/123.htm"
        data = parse_html(MOCK_69SHU_HTML, self.expected_69shu_config, url)

        self.assertEqual(data["chapter_title"], "第123章 The Title")
        self.assertEqual(data["chapter_number"], 123)
        self.assertEqual(data["next_chapter_url"], "https://www.some69shudomain.com/book/123/457.htm")
        
        # Check that cleanup selectors worked
        self.assertNotIn("Some info to be removed", data["content"])
        self.assertNotIn("An ad to be removed", data["content"])
        self.assertNotIn("Another ad", data["content"])
        self.assertNotIn("A content ad", data["content"])
        self.assertIn("This is the first paragraph", data["content"])

    def test_parse_html_1qxs(self):
        """Tests parsing logic for a 1qxs.com-like page."""
        url = "https://1qxs.com/some/path"
        data = parse_html(MOCK_1QXS_HTML, self.expected_1qxs_config, url)

        self.assertEqual(data["chapter_title"], "124：Another Title")
        self.assertEqual(data["chapter_number"], 124)
        self.assertEqual(data["next_chapter_url"], "https://1qxs.com/novel/45/45679.html")
        
        # Check that cleanup and content selection worked
        self.assertIn("First paragraph for 1qxs", data["content"])
        self.assertIn("Some other random text", data["content"])
        self.assertNotIn("本章未完，点击", data["content"])
        # Check that only <p> tags are included
        self.assertTrue(data["content"].startswith("<p>"))

if __name__ == '__main__':
    unittest.main() 