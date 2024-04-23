
--- Overview ---
This script loads stock history data from various sources and
  uses the data as input to a neural network for forcasting stock movement
Spoiler alert: the model did not produce accurate results and has limited predictive value
- Main script steps:
  Get stock data (daily returns, quarterly earnings\dividends\revenue\profit margin) from web
  Get economic information for training day - stock sector, month, election cycle, yield curve
  Store stock data to json files
  Load stock data from json files (web not needed)
  Generate sample\prediction collection
  Store s\p data in shelve file (single file)
  Load s\p data from shelve file
  Create model
  Run training

--- Notes ---
The sample data is from stocks in the S&P 500 across 5 years
For each stock, weekly returns a generated
A monthly return is calculated for the month following the sample (this is the forcast)
A sample is 100 weeks (2 years of market days)
The sample range is shifted 1 week to create the next sample
Total shifts per stock is (5yrs-2yrs-1month)x(50 weeks) = 140
Total samples (5 years) = (stock count) x (shift count) = 500x140 = 70000
Due to additional SP500 stocks, actual sample count is 71336
A single sample has 216 values (stock returns, SP returns, economic data)
Based on initial testing, no model could effectively predict stock direction
At the end of the script, there are nested loops to run multiple model configurations
    I estimate it will take over 50 days to run all configurations
