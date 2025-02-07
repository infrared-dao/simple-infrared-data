#!/usr/bin/env python3
import subprocess
from decimal import Decimal

# RPC and contract addresses
RPC_URL = "https://rpc.berachain.com/"
BGT_ADDRESS = "0x656b95E550C07a9ffe548bd4085c72418Ceb1dba"
INFRARED_ADDRESS = "0xb71b3DaEA39012Fb0f2B14D2a9C86da9292fC126"
IBGT_ADDRESS = "0xac03CABA51e17c86c921E1f6CBFBdC91F8BB2E6b"

def run_cast(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def wei_to_ether(wei):
    return Decimal(wei) / Decimal('1000000000000000000')

def get_infrared_vault(staking_token):
    return run_cast(
        f'cast call {INFRARED_ADDRESS} "vaultRegistry(address)(address)" {staking_token} --rpc-url {RPC_URL}'
    )

def get_rewards_vault(infrared_vault):
    return run_cast(
        f'cast call {infrared_vault} "rewardsVault()(address)" --rpc-url {RPC_URL}'
    )

def get_balances(rewards_vault, infrared_vault):
    total = run_cast(
        f'cast call {rewards_vault} "totalSupply()(uint256)" --rpc-url {RPC_URL}'
    )
    total = wei_to_ether(total.split()[0])

    infrared = run_cast(
        f'cast call {rewards_vault} "balanceOf(address)(uint256)" {infrared_vault} --rpc-url {RPC_URL}'
    )
    infrared = wei_to_ether(infrared.split()[0])

    return total, infrared

def get_reward_data(rewards_vault):
    # Get the overall BGT reward rate (BGT/sec) for this vault.
    rate = run_cast(
        f'cast call {rewards_vault} "rewardRate()(uint256)" --rpc-url {RPC_URL}'
    )
    raw_rate = Decimal(rate.split()[0])
    # Scale down by 1e18 twice (per your original conversion)
    reward_rate = raw_rate / Decimal('1000000000000000000') / Decimal('1000000000000000000')
    return reward_rate

def get_ibgt_rate(infrared_vault):
    try:
        result = run_cast(
            f'cast call {infrared_vault} "rewardData(address)(address,uint256,uint256,uint256,uint256,uint256,uint256)" {IBGT_ADDRESS} --rpc-url {RPC_URL}'
        )
        values = result.split('\n')  # Assume values are returned on separate lines.
        # Assume the IBGT rate is on the fourth line (index 3); adjust if necessary.
        rate_str = values[3].split('[')[0].strip()
        return Decimal(rate_str) / Decimal('1000000000000000000')
    except Exception as e:
        print(f"Error parsing IBGT rate from result '{result}': {e}")
        return Decimal('0')

def get_max_lengths(data):
    # For the table we need: Token Symbol, Stake %, BGT/sec, IBGT/sec.
    column_maxes = {
        'symbol': len('Token Symbol'),
        'stake': len('Stake %'),
        'bgt': len('BGT/sec'),
        'ibgt': len('IBGT/sec'),
    }
    for row in data:
        column_maxes['symbol'] = max(column_maxes['symbol'], len(str(row['symbol'])))
        column_maxes['stake'] = max(column_maxes['stake'], len(f"{row['stake']:.2f}%"))
        column_maxes['bgt'] = max(column_maxes['bgt'], len(f"{row['bgt']:.8f}"))
        column_maxes['ibgt'] = max(column_maxes['ibgt'], len(f"{row['ibgt']:.8f}"))
    return column_maxes

# List of staking tokens – each token corresponds to its own rewards vault.
STAKING_TOKENS = [
    "0xF961a8f6d8c69E7321e78d254ecAfBcc3A637621",
    "0xdE04c469Ad658163e2a5E860a03A86B52f6FA8C8",
    "0x38fdD999Fe8783037dB1bBFE465759e312f2d809",
    "0x2c4a603A2aA5596287A06886862dc29d56DbC354",
    "0xDd70A5eF7d8CfE5C5134b5f9874b09Fb5Ce812b4",
    # Add additional tokens as needed.
]

def main():
    data = []
    for token in STAKING_TOKENS:
        try:
            # Retrieve token symbol.
            symbol = run_cast(f'cast call {token} "symbol()(string)" --rpc-url {RPC_URL}')
            # Get the Infrared vault and its associated rewards vault.
            infrared_vault = get_infrared_vault(token)
            rewards_vault = get_rewards_vault(infrared_vault)

            # Retrieve TVL values.
            total_staked, infrared_stake = get_balances(rewards_vault, infrared_vault)
            # Get the overall BGT reward rate (BGT/sec).
            reward_rate = get_reward_data(rewards_vault)
            # Retrieve the IBGT reward rate.
            ibgt_rate = get_ibgt_rate(infrared_vault)

            # Compute the stake percentage: fraction of total supply held by the Infrared vault.
            stake_percentage = (infrared_stake / total_staked * 100) if total_staked > 0 else Decimal('0')
            # Compute the pro rata BGT/sec earned by the Infrared vault.
            ir_capture = reward_rate * (infrared_stake / total_staked) if total_staked > 0 else Decimal('0')

            data.append({
                'symbol': symbol,
                'stake': stake_percentage,
                'bgt': reward_rate,
                'ibgt': ibgt_rate,
                'ir_capture': ir_capture,  # For summary calculations
            })
        except Exception as e:
            print(f"Error processing {token}: {e}")

    if not data:
        print("No data to display.")
        return

    # Build the per-token table header.
    lengths = get_max_lengths(data)
    header = (
        f"| {'Token Symbol':<{lengths['symbol']}} | "
        f"{'Stake %':^{lengths['stake']}} | "
        f"{'BGT/sec':^{lengths['bgt']}} | "
        f"{'IBGT/sec':^{lengths['ibgt']}} |"
    )
    separator = (
        f"|{'-'*(lengths['symbol']+2)}|{'-'*(lengths['stake']+2)}|"
        f"{'-'*(lengths['bgt']+2)}|{'-'*(lengths['ibgt']+2)}|"
    )

    print(header)
    print(separator)

    total_bgt_emitted = Decimal('0')
    total_ir_captured = Decimal('0')
    total_ibgt = Decimal('0')

    for row in data:
        print(
            f"| {row['symbol']:<{lengths['symbol']}} | "
            f"{row['stake']:>{lengths['stake']-1}.2f}% | "
            f"{row['bgt']:>{lengths['bgt']}.8f} | "
            f"{row['ibgt']:>{lengths['ibgt']}.8f} |"
        )
        total_bgt_emitted += row['bgt']
        total_ir_captured += row['ir_capture']
        total_ibgt += row['ibgt']

    print(separator)

    # Summary data:
    print(f"Total BGT/sec emitted:               {total_bgt_emitted:.8f}")
    print(f"Total BGT/sec captured by Infrared:  {total_ir_captured:.8f}")
    capture_pct = (total_ir_captured / total_bgt_emitted * 100) if total_bgt_emitted > 0 else Decimal('0')
    print(f"Infrared Capture Percentage:         {capture_pct:.2f}%")

    # Additional data points:
    print(f"Total IBGT/sec:                      {total_ibgt:.8f}")
    overall_ibgt_captured_pct = (total_ibgt / total_ir_captured * 100) if total_ir_captured > 0 else Decimal('0')
    print(f"Overall IBGT/BGT captured (%):       {overall_ibgt_captured_pct:.2f}%")
    overall_ibgt_total_pct = (total_ibgt / total_bgt_emitted * 100) if total_bgt_emitted > 0 else Decimal('0')
    print(f"Overall IBGT/Total BGT (%):          {overall_ibgt_total_pct:.2f}%")

if __name__ == "__main__":
    main()
