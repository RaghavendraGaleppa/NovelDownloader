### Translation Process

This document outlines the database-driven workflow for translating novel chapters, as implemented in `src/translation/translator.py`.

#### Feature Overview

The translation process has been refactored to be entirely database-driven, replacing the previous file-based system. This new approach uses MongoDB to track the state of every chapter, ensuring that translations are efficient, resumable, and less error-prone. The `tool.py translate` command now orchestrates this new workflow.

---

#### Collections

Two main collections are used to manage the translation process:

1.  **`translation_progress`**: This collection stores a high-level summary for each novel's translation job. There is only one document per `novel_id`.

    *   `novel_id` (ObjectId): The ID of the novel being translated.
    *   `total_chapters` (int): The total number of raw chapters available for the novel.
    *   `completed_chapters` (int): A counter for how many chapters have been successfully translated.
    *   `last_updated_epoch` (float): The timestamp of the last update to this record.

2.  **`translated_chapters`**: This collection tracks the status of each individual chapter. Each chapter from the `raw_chapters` collection will have a corresponding document here.

    *   `novel_id` (ObjectId): The ID of the novel.
    *   `raw_chapter_id` (ObjectId): The ID of the corresponding record in the `raw_chapters` collection.
    *   `title` (str): The translated title of the chapter, derived from the first line of the translated content. Initially `None`.
    *   `status` (str): The current state of the translation (`in_progress`, `completed`, or `failed`).
    *   `pickup_epoch` (float): The timestamp when the chapter processing began.
    *   `end_epoch` (float): The timestamp when the translation process for the chapter concluded.
    *   `provider` (str): The name of the API provider that was used for the translation.
    *   `n_tries` (int): The number of times a translation has been attempted for this chapter.
    *   `saved_at` (str): The absolute path to the saved `.md` file containing the translated chapter.

---

#### Workflow

1.  **Initiation**: The process is started via `python tool.py translate --novel-title "Novel Name"`. The tool looks up the novel's ID from the `novels` collection.

2.  **Chapter Selection**:
    *   The system fetches all `_id`s from the `raw_chapters` collection for the given `novel_id`.
    *   It then finds all `raw_chapter_id`s in the `translated_chapters` collection that are marked with a `status` of `"completed"`.
    *   By finding the difference, it creates a list of chapters that still need to be translated.

3.  **Execution**:
    *   A `ThreadPoolExecutor` is used to process chapters in parallel, based on the `--workers` argument.
    *   For each chapter to be translated, the `_process_single_chapter_from_db` function is called.

4.  **Single Chapter Processing**:
    *   **Resume/Retry Logic**: The system first checks if a record for the `raw_chapter_id` already exists in `translated_chapters`.
        *   If it exists (indicating a previously failed attempt), it updates the record's status to `in_progress` and increments the `n_tries` counter.
        *   If it does not exist, a new record is created with a status of `in_progress`.
    *   **Content Fetching**: The raw chapter's content is read from the file path specified in the `saved_at` field of its `raw_chapters` record.
    *   **Translation**: The content is translated using the API.
    *   **Title Extraction**: The first line of the translated content is extracted to be used as the chapter title.
    *   **File Naming & Saving**: The translated content is saved to a file. The filename is standardized using the `chapter_number` from the `raw_chapters` record (e.g., `Chapter_00191.md`) to prevent errors from long or invalid characters.
    *   **Record Finalization**:
        *   On success, the corresponding `translated_chapters` record is updated with `status: "completed"`, the extracted title, the file path, and other metadata. The summary document in `translation_progress` is also updated.
        *   On failure, the record's status is set to `failed`. The chapter will be picked up again in a future run. 