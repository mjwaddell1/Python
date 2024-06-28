This code generates the Mandlebrot set. It uses a single thread or the threading module.

The threading library actually ran slower (2x) than a single thread. This is probably due to the GIL.

The application allows the user to select a portion of the fractal then zoom in (enter key). The space bar resets the image.

Process Explorer indicates additional threads being used so it's unclear why it runs slower with the threading library.

This the Python version used: Python 3.11.5 | packaged by Anaconda, Inc. | (main, Sep 11 2023, 13:26:23) [MSC v.1916 64 bit (AMD64)] on win32

Process Explorer - Single thread:
![image](https://github.com/mjwaddell1/Python/assets/35202179/53724d57-d491-4a7b-8ffe-ddcd407d4127)

Process Explorer - Multiple threads:
![image](https://github.com/mjwaddell1/Python/assets/35202179/c1f5760f-68dd-4974-9208-78c7a66fa424)

Initial image with selection rectangle:
![image](https://github.com/mjwaddell1/Python/assets/35202179/6b2631ef-10f6-4bcc-baa6-3e2c8853d8fd)

Rendering selection using multithreading:
![image](https://github.com/mjwaddell1/Python/assets/35202179/abdf4190-df33-4ed9-97c6-d825987fbcb0)

Rendered selection:
![image](https://github.com/mjwaddell1/Python/assets/35202179/1090a94f-df53-441a-8807-3d008a07a129)

Various captures:
![image](https://github.com/mjwaddell1/Python/assets/35202179/161bc11d-0d37-4f27-8cf5-a940a0eebe5d)

