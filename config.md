# Tag Audit Configuration

## abbreviate_tags

**Type:** Boolean (true/false)  
**Default:** false

When enabled, hierarchical tags will be abbreviated to show only the first and last parts of the hierarchy.

**Examples:**
- `grandparent::parent::child` becomes `grandparent::(...):child`
- `medical::cardiology::arrhythmia::afib` becomes `medical::(...):afib`
- Tags with only one or two levels are not abbreviated

This helps keep the tag audit dialog readable when you have deeply nested tag hierarchies.

**To enable:** Change the value to `true` in the Anki add-ons configuration window.
