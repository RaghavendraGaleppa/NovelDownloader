#!/bin/bash

# Script to migrate folder names from old to new naming convention
# Old: Novels/NovelTitle/Raws/ and Novels/NovelTitle/TranslatedRaws/
# New: Novels/NovelTitle/NovelTitle-Raws/ and Novels/NovelTitle/NovelTitle-English/

NOVELS_DIR="./Novels"
RENAMED_COUNT=0
SKIPPED_COUNT=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Novel Folder Migration Script ===${NC}"
echo "Migrating folders from old naming convention to new convention..."
echo

# Check if Novels directory exists
if [ ! -d "$NOVELS_DIR" ]; then
    echo -e "${RED}Error: $NOVELS_DIR directory not found!${NC}"
    echo "Make sure you're running this script from the correct directory."
    exit 1
fi

# Function to rename a folder safely
rename_folder() {
    local old_path="$1"
    local new_path="$2"
    local description="$3"
    
    if [ -d "$old_path" ]; then
        if [ -d "$new_path" ]; then
            echo -e "  ${YELLOW}⚠️  Warning: $new_path already exists, skipping $description${NC}"
            return 1
        else
            if mv "$old_path" "$new_path" 2>/dev/null; then
                echo -e "  ${GREEN}✅ Renamed $description: $(basename "$old_path") → $(basename "$new_path")${NC}"
                return 0
            else
                echo -e "  ${RED}❌ Failed to rename $description${NC}"
                return 1
            fi
        fi
    else
        echo -e "  ${YELLOW}⏭️  $description folder not found, skipping${NC}"
        return 1
    fi
}

# Iterate through each novel directory
for novel_dir in "$NOVELS_DIR"/*; do
    # Skip if not a directory
    [ ! -d "$novel_dir" ] && continue
    
    # Get the novel name from the directory name
    novel_name=$(basename "$novel_dir")
    
    echo -e "${BLUE}📚 Processing novel: $novel_name${NC}"
    
    # Define old and new paths
    old_raws_dir="$novel_dir/Raws"
    new_raws_dir="$novel_dir/${novel_name}-Raws"
    old_translated_dir="$novel_dir/TranslatedRaws"
    new_translated_dir="$novel_dir/${novel_name}-English"
    
    # Track if any renames happened for this novel
    novel_renamed=false
    
    # Rename Raws folder
    if rename_folder "$old_raws_dir" "$new_raws_dir" "Raws folder"; then
        novel_renamed=true
    fi
    
    # Rename TranslatedRaws folder
    if rename_folder "$old_translated_dir" "$new_translated_dir" "TranslatedRaws folder"; then
        novel_renamed=true
    fi
    
    # Update counters safely
    if [ "$novel_renamed" = true ]; then
        RENAMED_COUNT=$((RENAMED_COUNT + 1))
    else
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
    fi
    
    echo
done

# Summary
echo -e "${BLUE}=== Migration Summary ===${NC}"
echo -e "${GREEN}📖 Novels with renamed folders: $RENAMED_COUNT${NC}"
echo -e "${YELLOW}⏭️  Novels skipped (no changes needed): $SKIPPED_COUNT${NC}"

if [ $RENAMED_COUNT -gt 0 ]; then
    echo -e "${GREEN}✅ Migration completed successfully!${NC}"
    echo
    echo -e "${BLUE}Updated folder structure:${NC}"
    echo "  • Raws → {NovelTitle}-Raws"
    echo "  • TranslatedRaws → {NovelTitle}-English"
else
    echo -e "${YELLOW}ℹ️  No folders needed migration.${NC}"
fi

echo
echo -e "${BLUE}💡 Remember to update your command paths:${NC}"
echo "  • translator.py -n \"./Novels/YourNovel\""
echo "  • epub_converter.py -f \"./Novels/YourNovel/YourNovel-English\"" 