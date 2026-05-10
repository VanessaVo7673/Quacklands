Legend of the First Flock
An Interactive-Story created on PyGame
Vanessa Vo
(no citations or references because ideas are original or learnt through this course)
Version History
Version
Date
Description of Changes
0.1
01/25/2026
Start of game design
0.2
03/04/2026
Building base game
1.0
04/07/2026
Release of story
1. Overview
1.1. High Concept
Legend of the First Flock is a 2D interactive story built in PyGame. The player controls the “chosen” duck who must restore balance to Quacklands after the Great Plumage destroyed it. The game contains 4 mini games in which the player will have a chance to recover a stolen element at each level. The goal of this game will be to complete each chapter and bring peace back to the land.
2. Changes from Original Design
2.1. Big Adjustments
Since the previous submission, the project has evolved from a single implemented mini-game into an actual interactive story with multiple chapters.
New additions/improvements include:
-
A JSON story system
-
Complete chapters
-
Multiple minigames:
o
Chapter 1: Dodge and collect
o
Chapter 2: Drag and drop puzzle
o
Chapter 3: Memory game
o
Chapter 4: Tic-Tac-Toe (Final)
Instead of hardcoding game flow, the program now dynamically loads scenes from a JSON file, making the system more flexible and scalable.
2.2. Structural Improvements
-
Improved state management system
-
Separated logic into modular components:
o
UI
o
story rendering
o
gameplay systems
-
Added reusable systems for:
o
buttons
o
scene transitions
o
puzzle handling
-
Implemented multiple gameplay mechanics within one unified system
These changes made the program significantly more organized, easier to debug, and easier to expand.
2.3. Asset Developments
In the game I ended up drawing way more assets than anticipated! This includes a wide variety of custom art such as:
-
Backgrounds for each chapter
-
Element-themed visuals
-
UI elements (buttons, banners, lives)
-
Card graphics for memory game
-
Puzzle pieces for drag-and-drop game
-
Animations such as the glow
Assets were organized into chapter-specific folders, improving readability and structure.
3. Program Structure
3.1. Overall Program Flow/Algorithm
The program follows a state-based and data-driven architecture, where the JSON file controls the progression of scenes and gameplay.
3.2. Program Flow:
1.
Initialize PyGame
2.
Load assets (images, fonts, sounds)
3.
Load and parse JSON story file
4.
Set current scene to "main_menu"
5.
Enter main loop:
-
Load current scene data
-
Display text, image, and UI
-
If scene contains choices:
o
Wait for user input
o
Transition to next scene
-
If scene contains a puzzle:
o
Launch corresponding mini-game
o
Check win condition
o
Award element
o
Continue progression
6.
Repeat until game ends
3.3. Algorithm:
Start program → Initialize PyGame → Load JSON data
Loop:
-
Get current scene
-
If menu → display options
-
If story → display dialogue
-
If puzzle → run gameplay
-
Update screen
-
Move to next scene
-
End when player quits
