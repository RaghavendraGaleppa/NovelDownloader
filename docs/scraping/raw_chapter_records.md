### Raw Chapter Records

This document outlines the functionality for creating individual records for each scraped chapter, as implemented in `src/scraping/parse_chapter.py`.

#### Feature Overview

Previously, scraped chapter data was stored directly in the `Raws` folder without a corresponding database entry to track metadata. This feature introduces a new collection in MongoDB called `raw_chapters` to store information about each scraped chapter.

#### `raw_chapters` Collection

After a chapter is successfully scraped and saved to a file, a new document is inserted into the `raw_chapters` collection.

##### Fields:

-   `novel_id` (ObjectId): The ID of the novel in the `novels` collection.
-   `progress_id` (ObjectId): The ID of the scraping session in the `scraping_progress` collection.
-   `chapter_number` (int): The chapter number of the scraped chapter.
-   `title` (str): The title of the scraped chapter.
-   `saved_at` (str): The absolute path to the saved chapter file.
-   `created_at` (datetime): The timestamp when the record was created.

#### Implementation Details

1.  A new function, `_create_raw_chapter_record`, has been added to `src/scraping/parse_chapter.py`.
2.  This function is responsible for creating and inserting the record into the `raw_chapters` collection.
3.  In the main scraping loop of the `main` function, after a chapter file is successfully created, the `_create_raw_chapter_record` function is called.
4.  The `progress_id` is now fetched when a scraping job is started or resumed and passed to the record creation function. 