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
![image](https://github.com/mjwaddell1/Python/assets/35202179/36740927-015c-4d97-92fd-2ca3199b7002)

Food found (by 2 ants), returning to nest:
![image](https://github.com/mjwaddell1/Python/assets/35202179/83d0850c-1c9a-4fd4-b63d-1d93d6a60ca2)

All ants feeding (big dot is 48 ants moving together):
![image](https://github.com/mjwaddell1/Python/assets/35202179/403482d5-bb14-4031-a5e0-3a0a6cbe0dfe)
