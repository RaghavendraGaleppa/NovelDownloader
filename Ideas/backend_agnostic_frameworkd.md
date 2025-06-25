# Backend-Agnostic Scraping Framework

## 1. Introduction

### Current Situation
The current scraping implementation relies on a system of `ExtractionBackend` classes (e.g., `EB69Shu`, `EB1QXS`). Each class is tailor-made for a specific website, containing hardcoded logic to parse that site's unique HTML structure. While effective, this approach is rigid and not easily scalable. Adding support for a new website requires writing a new Python class, which is time-consuming and clutters the codebase.

### Goal
The objective is to create a more flexible, data-driven framework that can handle various novel websites without requiring new Python code for each site. The framework should be "agnostic" to the website's specific implementation details, instead relying on a set of instructions to perform the extraction.

## 2. Core Problem
The fundamental challenge is to reliably identify and extract four key pieces of information from a chapter's HTML page, regardless of the site's structure:

1.  **Chapter Content:** The main text of the novel chapter.
2.  **Chapter Title:** The title of the current chapter.
3.  **Next Chapter URL:** The link to the following chapter to continue scraping.
4.  **Chapter Number:** A unique identifier for the chapter, used for ordering and filename generation.

Different websites use different HTML tags, class names, and IDs for these elements, which is why the current system needs specific backends.

## 3. Proposed Solution: Configuration-Driven Extraction
The most practical and robust solution is to move the extraction logic from Python code into external configuration files. Instead of a "backend class," each website would have a "backend configuration."

### The Concept
A single, generic scraper engine would be developed. This engine wouldn't know anything about "69shu" or "1qxs" directly. Instead, when given a URL, it would:
1.  Identify the domain (e.g., `www.69shu.com`).
2.  Load a specific configuration file or object associated with that domain.
3.  Use the rules defined in the configuration to parse the HTML.

### Configuration File Structure
A JSON or YAML file would be ideal for storing these configurations. This file would act as a registry of supported websites.

Here is an example of what a configuration for `69shu.com` and `1qxs.com` might look like in a `selectors.json` file:

```json
{
  "www.69shu.com": {
    "next_chapter_url": {
      "selector": "div.page1 a",
      "text_contains": "下一章",
      "attribute": "href"
    },
    "chapter_title": {
      "selector": "div.txtnav h1"
    },
    "content_container": {
      "selector": "div.txtnav",
      "cleanup_selectors": [
        "#txtright", 
        ".bottom-ad",
        ".contentadv", 
        ".txtinfo", 
        ".page1"
      ]
    },
    "chapter_number": {
      "selector": "div.txtnav h1",
      "regex": "第(\\d+)章"
    }
  },
  "www.1qxs.com": {
    "next_chapter_url": {
      "selector": "#next",
      "attribute": "href"
    },
    "chapter_title": {
      "selector": ".title h1"
    },
    "content_container": {
      "selector": "div.content",
      "content_element": "p",
      "cleanup_text_contains": [
        "本章未完，点击"
      ]
    },
    "chapter_number": {
      "selector": ".title h1",
      "regex": "^(\\d+)："
    }
  }
}
```

### Key Fields Explained:
- **`selector`**: A CSS selector to find the target element(s).
- **`text_contains`**: (Optional) Narrows down elements from the selector by checking if their text contains a specific string (e.g., finding the "Next Chapter" link among other navigation links).
- **`attribute`**: (Optional) Specifies which attribute of the element to get the value from (e.g., `href` for an `<a>` tag). If not present, the text content is used.
- **`cleanup_selectors`**: (Optional) A list of CSS selectors for elements that should be removed from the content block before extraction (e.g., ads, recommendations, navigation).
- **`cleanup_text_contains`**: (Optional) A list of text strings. Any paragraphs containing this text will be discarded.
- **`regex`**: (Optional) A regular expression to apply to the extracted text or attribute value to get the final, clean data (e.g., extracting "123" from "Chapter 123").
- **`content_element`**: (Optional) For content blocks, this can specify the tag of the actual content (e.g. `<p>` tags) within the main container.

## 4. New Scraping Workflow
The `parse_chapter.py` logic would be refactored to follow this new workflow:

1.  Start with an initial URL.
2.  Extract the domain from the URL.
3.  Load the `selectors.json` file and find the configuration object for that domain. If not found, exit with an error.
4.  Fetch the HTML for the current chapter's URL.
5.  Pass the HTML and the domain's configuration object to a **Generic Parser**.
6.  The **Generic Parser** performs the following steps:
    a. **Next URL:** Uses the `next_chapter_url` selector and rules to find the link for the next chapter.
    b. **Title:** Uses the `chapter_title` selector to find the title.
    c. **Chapter Number:** Uses the `chapter_number` selector and regex to find the chapter number.
    d. **Content:**
        i. Finds the main `content_container`.
        ii. Removes any elements matching `cleanup_selectors`.
        iii. Extracts the text, potentially by iterating over `content_element` tags like `<p>`.
        iv. Discards any text blocks that match `cleanup_text_contains`.
7.  Save the cleaned, extracted content to a markdown file.
8.  If a "next chapter URL" was found, repeat the process from step 4 with the new URL.

## 5. Advantages of This Approach

- **Extensibility:** Adding a new website is as simple as adding a new entry to the JSON file after analyzing the site's HTML. No Python code needs to be touched.
- **Maintainability:** If a website changes its layout, the fix is a quick update to its JSON configuration, not a code deployment.
- **Simplicity:** The core Python logic becomes much simpler and more focused. It's just an engine for executing rules, not a complex web of site-specific logic.
- **User Contribution:** It's much easier for non-developer users to contribute new website configs by creating and sharing JSON snippets.

## 6. Advanced Future Idea: Heuristic-Based Extraction
Far in the future, a "zero-config" system could be explored. This would use heuristics to *guess* the correct elements:
- **Next Link:** Look for `<a>` tags with text like "Next", "下一章", "下页".
- **Content:** Find the `<div>` on the page with the highest text-to-tag ratio (the most text content).
- **Title:** Assume the `<h1>` or `<title>` tag is the chapter title.

This approach is significantly more complex and prone to errors, but could be an interesting enhancement on top of the robust configuration-driven framework. The configuration-driven model is the recommended and most immediately beneficial path forward. 

## 7. Handling Unsupported Websites

A critical aspect of the framework is how it behaves when a user provides a URL for a website that is not defined in the configuration file (e.g., `selectors.json`).

### The "Fail Gracefully" Approach (Recommended)
The recommended and most robust initial approach is to fail gracefully with a clear and informative error message.

The workflow would be:
1.  The scraper receives a starting URL.
2.  It extracts the domain from the URL (e.g., `www.new-novel-site.com`).
3.  It attempts to look up this domain in the `selectors.json` configuration.
4.  **If the domain is not found:**
    *   The scraper stops execution.
    *   It prints a message to the console, for example:
        ```
        ❌ Error: Website 'www.new-novel-site.com' is not supported.
        
        💡 To add support for this website, please add a new configuration entry for it in 'selectors.json'.
        
        You can use the existing entries as a template. You will need to inspect the website's HTML to find the correct CSS selectors for the content, title, and next chapter link.
        ```
5.  **If the domain is found:**
    *   The scraper proceeds with the normal workflow.

This approach has several advantages:
-   **Predictable:** The tool's behavior is clear and consistent. It avoids trying to "guess" and potentially scraping incorrect data or getting into an infinite loop.
-   **Empowering:** It directly informs the user *why* it failed and *how* they can fix it. This encourages user contributions and makes the tool more powerful for the end-user.
-   **Simple to Implement:** It requires a straightforward check at the beginning of the scraping process.

### Future Enhancement: Interactive Configuration Wizard
As a future enhancement, an interactive wizard could be developed. If a site is unsupported, the tool could ask the user if they want to create a configuration on the fly. It would prompt them for the necessary selectors one by one. While very user-friendly, this adds significant complexity and is best considered as a feature to be built on top of the solid "fail gracefully" foundation. 