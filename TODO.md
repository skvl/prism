# FIXMEs

## F1. TUI open/init wizard TAB-completion

When user inputs path to vault it should allow to tab complete it. E.g. with
`/tm` with `TAB` it should complete to `/tmp/`. If several variants exist then
it should display them all like `zsh`.

Also I want with `ENTER` press use path from input. Currently I have to TAB to
select one of buttons `open` or `init`.

## F2. New node wizard should provide path input

## F3. All nodes without path must have `/` path by default

This changes the core, CLI and TUI. Alsow you should update README and
specifications.

## F4. Query tab not working

I could select type and tags but there is no search button. So Results is empty
after I input data for query.

## F5. Low test coverage for core, cli and tui

Check what is current test coverage and what could we do better. I would prefer
to have coverage 90%+.

# Proposals

## P1. Obsidian like editor

With Obsidian one could press `[[` and get list of articles to link with. More
over one could use `#` to link with section by header and `^` with some text in
article. Or using `![[` allows to insert images or even documents with preview.
I would like to add simple `nano` like editor with such features.

I would like that this new editor provide raw and view modes. In raw
mode when user builds table it is shown as is in raw markdown. In randered mode
the tables are visulalized. The same idea for other markdown features. E.g.
links. Use Obsidian as reference.

This sould be a separate project. So other projects like CLI/TUI/GUI could work
with it.

## P2. Folder nodes

Prism supports only file-based data blobs (`.pdf`, `.md`, etc.). User could want
to store folder with data in Prism. E.g. source code folder with subfolder and
code files.

In such case I feel that it is natural to place whole folder as "data" inside
`path/from/uuid`. But it should support sync feature. So application must detect
changes in folder.

Metadata should olso support ignore patters like ".gitignore". E.g. folder
contains ".git" subfolder. And user don't want to sync it. So ".git" should be
listed in ignore patterns.

## P3. Data import in TUI

TUI doesn't support import. But it is natural for user to import article data or
some other artifact. For that I could see to variants:

- Import wizard where user could navigate through file system, select artifact
  to import, add description, links, paths, tags, etc.
- Two panel mode like midnight commander where one panel could show hosts file
  system. And user could run "Copy" or "Move" command.
  - Such command must open window to set properties for the command like in
    import wizard.

May be there exists other good workflows and UI/UX decicions. We should select
the best one.

## P4. Password manager

It seems natural to store passwords in single manager with all other data. The
good password manager for reference is KeePassXC. It could store a lot of data:
searchable title, username and password, URL, description, additional files and
key-value storage.

I think Prism could add new type of node like `password`. Password should
provide a new set of properties to store title, username and password, etc. like
KeePassXC. It is worth to consider the agile properties feature for every node.

But we should carefully select what should be open and what must be encrypted.
E.g. username and password must be encrypted. But title, tags, may be
description should be open to be able searchable.

## P5. Tasks management

I think that "tasks" are naturally calendar events with som properties. The
Obsidian's Tasks plugin is good reference.

**TODO** Continue

## P6. Backup to local path

**TODO** Continue

## P7. Encrypted backup to local path

**TODO** Continue

## P8. Encrypted backup to remote

**TODO** Continue
