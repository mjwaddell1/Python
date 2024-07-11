This code generates the Mandlebrot set. It uses a single thread or the threading module. This is a good candidate for multi-threading since each point value is calculated independently. There are additional scripts that use multiple processes or web services.

The execution time using the threading library is about the same as using a single thread. This is probably due to the GIL and true multithreading is not currently supported in Python.

The application allows the user to select a portion of the fractal then zoom in (enter key). The space bar resets the image. The left\right arrows are used to traverse through the render history. Escape exits the script.

Process Explorer indicates additional threads being used so it's unclear why the threading library does not improve render speed.

Using multi-process (FractalProcess.py) decreased the render time (50 vs 14 seconds) though code complexity increased. CPU utilization rose to 100% using all cores.

Using multiple web services (FractalWeb.py) increased render time (20 seconds) on a single machine. The architecture allows multiple machines to be used which could significantly reduce render time. Note that a single thread is used per service instance.

Python version used: Python 3.11.5 | packaged by Anaconda, Inc. | (main, Sep 11 2023, 13:26:23) [MSC v.1916 64 bit (AMD64)] on win32

Process Explorer - Single thread:
![image](https://github.com/mjwaddell1/Python/assets/35202179/53724d57-d491-4a7b-8ffe-ddcd407d4127)

Process Explorer - Multiple threads:
![image](https://github.com/mjwaddell1/Python/assets/35202179/c1f5760f-68dd-4974-9208-78c7a66fa424)

Process Explorer - Multiple processes:
![image](https://github.com/mjwaddell1/Python/assets/35202179/8c4c6a9f-7879-4697-b63d-7d4262db19a4)

For reference - CPU usage remained low using multi-threading during the render process:
![image](https://github.com/mjwaddell1/Python/assets/35202179/7d565db5-4a98-4b67-bb7c-291fa82c98e3)

For reference - CPU usage went to 100% using multiple processes during the render process:
![image](https://github.com/mjwaddell1/Python/assets/35202179/8cbc01bb-009f-4d0c-9d56-8c87423a2d26)

Initial image with selection rectangle:
![image](https://github.com/mjwaddell1/Python/assets/35202179/6b2631ef-10f6-4bcc-baa6-3e2c8853d8fd)

Rendering selection in progress (multi-threading):
![image](https://github.com/mjwaddell1/Python/assets/35202179/abdf4190-df33-4ed9-97c6-d825987fbcb0)

Render complete:
![image](https://github.com/mjwaddell1/Python/assets/35202179/1090a94f-df53-441a-8807-3d008a07a129)

Various captures:
![image](https://github.com/mjwaddell1/Python/assets/35202179/0c58ab8d-0072-4f40-a43a-30ec664af403)

