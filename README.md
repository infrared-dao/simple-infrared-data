# simple-infrared-data
# Infrared Vault Rewards Monitor

## Features
- Fetches Infrared vault and rewards vault for each staking token.
- Retrieves token balances and calculates stake percentages.
- Queries reward rates for BGT and IBGT tokens.
- Computes total emissions and reward capture rates.
- Formats data into a readable table output.

## Requirements
- Python 3
- `cast` CLI (from Foundry)
- Access to an Berachain RPC endpoint

## Usage
1. Ensure `cast` is installed and configured.
2. Have python3 installed.
3. Replace the `RPC_URL` variable in `data.py` with the Berachain RPC endpoint if you have faster one.
4. Run the script:
 
  ```sh
   python3 data.py
  ```
