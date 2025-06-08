-- File: prefix_chapter_titles.lua
local chapter_count = 0

function Header (elem)
  -- We only want to modify the very first H1 encountered for each file/section
  -- that Pandoc processes sequentially from the input list.
  if elem.level == 1 then
    chapter_count = chapter_count + 1
    
    -- Create the prefix, e.g., "Chapter 001 - "
    -- Adjust padding (%03d) if you have more than 999 chapters.
    local prefix_text = string.format("Chapter %03d - ", chapter_count)
    local prefix_node = pandoc.Str(prefix_text)
    
    -- Prepend the prefix string to the existing header content.
    -- elem.content is a list of inline elements.
    table.insert(elem.content, 1, prefix_node)
    
    -- Return the modified header.
    return elem
  end
  -- Return other headers (H2, H3, etc., or subsequent H1s if any) unchanged.
  return elem
end 