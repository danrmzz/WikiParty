## Demo Video:
[![Watch the demo](https://img.youtube.com/vi/nXK9TCG8yMM/maxresdefault.jpg)](https://www.youtube.com/watch?v=nXK9TCG8yMM)

## Inspiration:
We wanted to create an engaging multiplayer game that combines knowledge and strategy, where players race from one random Wikipedia page to another using only the hyperlinks on each page. Instead of everyone just pulling up Wikipedia on their own browsers, our game creates a shared, synchronized experience where all players start at the same time and work toward the same goal. This setup makes the competition more exciting, with built-in features like timers and click tracking, offering a far more structured and dynamic challenge than simply browsing on your own.

## What we learned:
- Creating a GUI with PyQt5
- Creating a virtual machine to host a global server
- Data cleanup and parsing
- Compatibility with various operating systems
- Pair programming via version control
- Compromising between developer experience, expertise, and interests

## How we built our project:
- Expanding functionality and design from singleplayer to multiplayer with sockets
- Imported custom assets for improved user experience
- API integration
- Dividing complex goals into smaller subtasks that can be worked on by different groups

## Challenges we faced:
- **Choosing the Right Technology Stack Within a Time Limit**: With only 36 hours during the hackathon, we had to quickly decide on the tools and libraries that would allow us to build the game efficiently, balancing development speed with the complexity of multiplayer integration.
- **Getting Familiar with PyQt5 Syntax**: We faced a learning curve with PyQt5’s syntax, especially when managing complex layouts, signals/slots, and multi-threading within the interface.
- **Embedding a Website Inside a Desktop GUI**: Integrating Wikipedia pages using QWebEngineView within the PyQt5 application was tricky, especially ensuring it worked seamlessly with the game's logic and navigation.
- **Dealing with Server-Client Connectivity Issues**: Ensuring real-time communication between players and the server was challenging, particularly when handling socket errors, connection drops, and synchronizing data during multiplayer gameplay.
