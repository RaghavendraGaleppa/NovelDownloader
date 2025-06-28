### Raw Chapter Records

This document outlines the functionality for creating individual records for each scraped chapter, as implemented in `src/scraping/parse_chapter.py`.

#### Feature Overview

Previously, scraped chapter data was stored directly in the `Raws` folder without a corresponding database entry to track metadata. This feature introduces a new collection in MongoDB called `raw_chapters` to store information about each scraped chapter.

#### `scraping_progress` Collection Enhancement

To better organize raw chapter files, a new field has been added to the `scraping_progress` collection:

-   `raws_folder` (str): Stores the absolute path to the directory where raw chapter files for a specific novel are saved. This defaults to a `Raws` subfolder within the main novel directory (e.g., `Novels/My_Novel/Raws`).

When a scraping session is resumed, the script uses this path to save new chapters.

#### `raw_chapters` Collection

After a chapter is successfully scraped and saved to a file, a document is either created or updated in the `raw_chapters` collection. This system now supports chapters that are split into multiple parts on the source website.

##### Fields:

-   `novel_id` (ObjectId): The ID of the novel in the `novels` collection.
-   `progress_id` (ObjectId): The ID of the scraping session in the `scraping_progress` collection.
-   `chapter_number` (int): The chapter number of the scraped chapter.
-   `title` (str): The title of the scraped chapter.
-   `saved_at` (str): The absolute path to the saved chapter file.
-   `created_at` (datetime): The timestamp when the record was first created.
-   `updated_at` (datetime): The timestamp when the record was last updated (e.g., when a new part was added).
-   `n_parts` (int): A counter for the number of parts a chapter has. For a standard chapter, this will be `1`. If a chapter is split into multiple web pages, this number will be incremented for each part scraped.

#### Implementation Details

1.  The `_create_raw_chapter_record` function has been replaced with `_upsert_raw_chapter_record` in `src/scraping/parse_chapter.py`.
2.  This function uses a MongoDB `update_one` operation with `upsert=True`.
    -   If a record for a given `novel_id` and `chapter_number` does not exist, it is created with `n_parts` set to `1`.
    -   If a record already exists, it simply increments the `n_parts` field and updates the `updated_at` timestamp.
3.  In the `main` function, the script now determines the output directory by checking for the `raws_folder` field in the novel's progress document. 