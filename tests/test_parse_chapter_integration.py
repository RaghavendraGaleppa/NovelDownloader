import unittest
import os
import shutil
import argparse
from src.scraping.parse_chapter import main as scrape_main

class TestParseChapterIntegration(unittest.TestCase):
    
    # Define test-specific variables
    test_output_base_dir = "tests/test_output"
    test_title_69shu = "TestNovel69Shu"
    test_title_1qxs = "TestNovel1QXS"
    
    # URLs provided by the user
    url_69shu = "https://www.69shuba.com/txt/88724/39943182"
    url_1qxs = "https://www.1qxs.com/xs/228/1.html"

    def setUp(self):
        """Create a temporary directory for test output."""
        os.makedirs(self.test_output_base_dir, exist_ok=True)

    def tearDown(self):
        """Clean up the test output directory."""
        if os.path.exists(self.test_output_base_dir):
            shutil.rmtree(self.test_output_base_dir)

    def test_scrape_69shu_single_chapter(self):
        """Integration test for scraping a single chapter from 69shuba.com."""
        args = argparse.Namespace(
            url=self.url_69shu,
            max_chapters=1,
            output_dir=None,
            start_chapter=None,
            title=None, # Let the scraper determine the title
            output_path=self.test_output_base_dir,
            no_progress=True
        )
        scrape_main(args)
        
        # Check that at least one subdirectory was created
        subdirs = [d for d in os.listdir(self.test_output_base_dir) if os.path.isdir(os.path.join(self.test_output_base_dir, d))]
        self.assertTrue(len(subdirs) >= 1, "No output directory was created.")
        
        # Check that a file was created in the first subdirectory found
        output_dir = os.path.join(self.test_output_base_dir, subdirs[0])
        files = os.listdir(output_dir)
        self.assertEqual(len(files), 1, "Expected exactly one file in the output directory.")
        
        file_path = os.path.join(output_dir, files[0])
        self.assertTrue(os.path.getsize(file_path) > 0, "The created chapter file is empty.")

    def test_scrape_1qxs_single_chapter(self):
        """Integration test for scraping a single chapter from 1qxs.com."""
        args = argparse.Namespace(
            url=self.url_1qxs,
            max_chapters=1,
            output_dir=None,
            start_chapter=None,
            title=None, # Let the scraper determine the title
            output_path=self.test_output_base_dir,
            no_progress=True
        )
        scrape_main(args)
        
        # Check that at least one subdirectory was created
        subdirs = [d for d in os.listdir(self.test_output_base_dir) if os.path.isdir(os.path.join(self.test_output_base_dir, d))]
        self.assertTrue(len(subdirs) >= 1, "No output directory was created.")
        
        # Check that a file was created in the first subdirectory found
        output_dir = os.path.join(self.test_output_base_dir, subdirs[0])
        files = os.listdir(output_dir)
        self.assertEqual(len(files), 1, "Expected exactly one file in the output directory.")
        
        file_path = os.path.join(output_dir, files[0])
        self.assertTrue(os.path.getsize(file_path) > 0, "The created chapter file is empty.")

if __name__ == '__main__':
    unittest.main() 