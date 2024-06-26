This is a simple machine learning experiment.<br/>

100 samples (X) are generated. Each sample has 3 values:
- A random number
- The counter value (0-99)
- Odd\even flag  (counter%2)

The predictor (Y) is the odd\even flag  (matches X IsOdd)<br/>

![image](https://github.com/mjwaddell1/Python/assets/35202179/3ec7d602-0cba-4893-babe-494ac451277f)

Question: Will the neural network ignore the random value during training?<br/>

Based on several runs, the random value is not ignored and full training is not achieved.<br/>
Replacing the random value with a constant (0) produces correct training.<br/>
The counter value is ignored.

With random value (note small cost range):

![image](https://github.com/mjwaddell1/Python/assets/35202179/e2551380-3ad1-44d0-a86a-94957a0e7034)

With constant:

![image](https://github.com/mjwaddell1/Python/assets/35202179/0502ac0e-a00b-4ced-8e38-021028bb08bd)

With all values X = Y:

![image](https://github.com/mjwaddell1/Python/assets/35202179/61174007-1f6d-4600-a466-1c022219eca5)

