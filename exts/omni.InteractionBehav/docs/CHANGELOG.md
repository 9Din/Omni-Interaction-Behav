# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.4] - 2025-12-08
### Updated
- Update: Dynamic Root Path Detection
- Improvement: Recursive Search Algorithm
- Enhancement: Error detection and other functions

## [2.0.3] - 2025-12-05
### Updated
- Performance considerations: Add caching mechanism
- Technical support: Supports paths in SUB USD
- Search restrictions: Improved search restrictions
- UI update: When searching for large amounts of data asynchronously, it is necessary to ensure UI responsiveness

### Added
- Add support for multiple door types

### Fixed
- Fixed the issue of naming sub scenes the same


## [2.0.2] - 2025-12-03
### Updated
#### Access Control:
- Updated dictionary
- Type check in update method
- Display messages in the update method
- Update relevant method names and comments
### Fixed
#### Access Control:
-Modify door type check logic

## [2.0.1] - 2025-12-02
### Fixed
#### Access Control:
- Distinguish between single leaf and double leaf sliding doors: Set different default sliding distances based on door type in the UI
- UI feedback: Clearly display door type and default sliding distance in status messages
- Slide range: Set a larger maximum sliding range for a single door

## [2.0.0] - 2025-12-01
### Updated
#### Major version update
- Add access control system (Make plugins more suitable for use in the field of architecture)

## [1.1.5] - 2025-11-28
### Changed
- Remove material management function
- Remove the solar path control function

## [1.1.4] - 2025-11-19
### Fixed
#### Material management:
- Repair and delete history management
- Improve deletion operation
- Enhance revocation function
- Improve error handling

## [1.1.3] - 2025-11-04
### Fixed
#### Material management scanning optimization:
- Improved ancestor material detection logic to reduce misjudgments
- Enhanced material usage detection, including more binding methods and relationships
- Added detailed debugging information output

## [1.1.2] - 2025-10-28
### Fixed
- Fuzzy search function for the root path of lighting
- Add input boxes for light attribute parameters

## [1.1.1] - 2025-10-27
### Updated
- Support undo deletion operation

### Fixed
- Fixed the issue of not being able to select materials
- Repair material selection management


## [1.1.0] - 2025-10-26
### Updated
#### Add material management:
- Click 'Scan Unused' to scan unused materials
- Select the material to be deleted
- Perform deletion operation

## [1.0.9] - 2025-10-23
### Updated
- Removed unnecessary imports and unused variable declarations
- Retained core error handling and removed redundant printing statements
- Removed debugging and uncalled build methods
- Removed unused solar operation methods
- Retained all necessary styles and removed duplicate definitions
- Maintained the core USD attribute setting method and removed duplicate code
- Simplified state variable management

## [1.0.8] - 2025-10-22
### Updated
- Modify the Sun Light detection mechanism and remove Create New Distant Light
- Update DistantLight attribute control
- Update precise input box

## [1.0.7] - 2025-10-21
### Updated
- New buttons have been added to the UI: "Record Defaults" and "Reset to Defaults"

## [1.0.6] - 2025-10-20
### Changed
- Removed color temperature slider
- Remove color slider
- Updated the sub level and deeper level lighting control functions of the 'Lighting Group'

## [1.0.5] - 2025-10-13
### Fixed
- Fixed float division by zero issue

## [1.0.4] - 2025-10-12
### Security
- Removed usage of omni.kit.ui
- Improvement in security

## [1.0.3] - 2025-10-11
### Changed
- Update the public API for the extension

## [1.0.2] - 2025-10-10
### Changed
- Fix the auto save to be window irrelevant (when progress bar window or timeline window is closed, still working), save to "${cache}/activities", and auto delete the old files, at the moment we keep 20 of them
- Add file numbers to timeline view when necessary
- Add size to the parent time range in the tooltip of timeline view when make sense
- Force progress to 1 when assets loaded
- Fix the issue of middle and right clicked is triggered unnecessarily, e.g., mouse movement in viewport
- Add timeline view selection callback to usd stage prim selection

## [1.0.1] - 2025-10-10
### Fixed
- test failure due to self._addon is None

## [1.0.0] - 2025-10-09
### Added
- Initial window

 