# Tag Audit for Anki

## Use Case
I needed a way to quickly see which tags were used in a selection of notes, and exclude notes which have certain tags.

Specifically this was to see which notes in added:1 were already tagged, and which still needed processing. Also useful for checking if I accidentally put incorrectly tagged cards in the wrong deck, or when bulk tagging I had tagged some notes twice with different topics (it happens sometimes when selecting multiple notes from a list, I use the mark function to distinguish processed notes but accidents happen).

## Features

* **Visual Tag Summary**: Instantly view all tags contained within your current selection, sorted alphabetically with their occurrence counts.
* **Interactive Filtering**: Click any tag to "exclude" it. This automatically updates your browser search to filter out notes containing that tag, helping you narrow down selections efficiently.
* **Smart Tag Abbreviation**: Toggle the "Abbreviate tags" checkbox to shorten long hierarchical tags (e.g., `Medical::Pathology::Cardiology` becomes `Medical::(...)::Cardiology`) for cleaner viewing.

## Usage

1.  Open the **Anki Browser**.
2.  Select a group of cards/notes.
3.  Go to **Notes** > **Tag Audit** in the top menu bar, or press the shortcut `Ctrl+Shift+T`.
4.  The Tag Audit window will appear:
    * **Click** a tag to exclude it from your current selection.
    * **Check/Uncheck** "Abbreviate tags" at the top to toggle hierarchical shortening.

## Configuration

The addon automatically saves your preference for tag abbreviation.
