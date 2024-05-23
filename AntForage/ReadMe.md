This script simulates ants foraging for food<br/>
Ants leave nest in random directions and repeat until food is found<br/>
The food trail is used by the other ants until food is moved<br/>
When food is moved, ants must return to nest to get new food trail<br/>
Notes:<br/>
   - Ants will return to the nest if no food found
   - Ants don't look for new food during return trip
   - Latest found food path is used by rest of colony, previous paths are deactivated
   - Food path may not be the most direct route, just latest path found
   - Multiple ants may be at same position, so single dot shown (ant overlap)

Initial search:
![image](https://github.com/mjwaddell1/Python/assets/35202179/a594b150-1cd7-417e-8478-fbfbf892a33a)

Food found (by 2 ants), returning to nest:
![image](https://github.com/mjwaddell1/Python/assets/35202179/01296801-5640-4eb2-a558-941e0d25f1f5)

All ants feeding (pink dot is 48 ants moving together):
![image](https://github.com/mjwaddell1/Python/assets/35202179/48ca9e62-e98e-4981-8b5e-f84ac70bae57)
