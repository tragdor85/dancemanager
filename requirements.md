# Dance Manager System Requirements

## Data Import
- Import dance classes from CSV: column header is the class name, each row below it lists a student in that class
- Import dance teams from CSV: column header is the team name, each row below it lists a dancer on that team

## Dancers
- Add individual dancers. Each dancer can be assigned to one team

## Classes
- Add teams of dancers to one or more dance classes
- Add individual dancers to each class, regardless of what team the dancer is on

## Dances
- Add dances that can include dance class members and/or individual dancers. Each dance has a song name and an optional instructor

## Instructors
- Add instructors that can be assigned to lead a dance class and multiple dances

## Recital Organization
- Automatically identify which dancers are in what dance and produce a dance schedule that ensures each dancer has at least 4 dances between performances for costume changes

## Extensibility
- Allow adding other dance studio management features (e.g., schedules for which class meets in which studio at which time). Do not flesh these features out or add specific stubs yet — keep the data structures and design patterns flexible for future adjustments

## Technical Requirements
- Written in Python
- Data stored in a simple, easy-to-use data structure (JSON)
- Command-line interface to start; designed so a UI can be added later
- Most input and output in CSV format or text responses
