```
  Python scripts to handle client server
  connections with chatrooms
```

# Python Server-Client Chatrooms

**How to use:**

1. Start the server.py
2. Make sure the client side CONSTANTS.py contains the correct Addr and PORT info of the server
3. Start client-gui.py

To interact with servers and rooms you can use the following commands:

- /create
  Create a new room and join it,
  rooms are named room_i, where i
  is an incremented value on server side
- /qqq
  Close the application
- /join {room_id}
  join a specific room, no authentication required,
  if the room_id exists, user will be added to it
- /leave
  leave the current room you are in
- /username
  Set your username on the server size
- /users
  list the users in the current room
- /kick {username}
  Kick a user via their username
