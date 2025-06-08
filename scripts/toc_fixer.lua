-- File: toc_fixer.lua
local chapter_count = 0

function Header (elem)
  -- We assume the first H1 in each concatenated file is the chapter title.
  -- Pandoc concatenates the input markdown files before processing.
  if elem.level == 1 then
    chapter_count = chapter_count + 1
    
    -- Create the new H1 text, e.g., "Chapter 001"
    -- The %03d formats the number to be 3 digits, zero-padded.
    -- Adjust padding (e.g., %04d) if you have more than 999 chapters.
    local new_h1_content = {pandoc.Str(string.format("Chapter %03d", chapter_count))}
    
    -- Create the new H1 element.
    local new_h1 = pandoc.Header(1, new_h1_content) 
    
    -- Demote the original H1 to H2, keeping its original content and attributes.
    local original_h1_as_h2 = pandoc.Header(2, elem.content, elem.attr)
    
    -- Return a list of elements to replace the original H1: 
    -- the new H1, then the original H1 (now an H2).
    return {new_h1, original_h1_as_h2}
  end
  -- Return other headers (H2, H3, etc., or subsequent H1s if any) unchanged.
  return elem
end
