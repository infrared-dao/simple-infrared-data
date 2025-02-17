#!/usr/bin/env python3
import subprocess
from decimal import Decimal

RPC_URL = "https://rpc.berachain.com/"

# Vault mappings
VAULTS = {
    "byUSD-HONEY": {
        "old": "0xd8c53e0E7CF3eCFE642a03A30EC30681eF4159a9",
        "new": "0xbbB228B0D7D83F86e23a5eF3B1007D0100581613"
    },
    "USDC.e-HONEY": {
        "old": "0x812e5ff20326743151e2efa02d89d488efd826c9",
        "new": "0x1419515d3703d8F2cc72Fa6A341685E4f8e7e8e1"
    },
    "WBERA-HONEY": {
        "old": "0xa95ff8097b0e405d1f4139f460fa4c89863784c0",
        "new": "0xe2d8941dfb85435419D90397b09D18024ebeef2C"
    },
    "WBERA-WBTC": {
        "old": "0x5614314Eef828c747602a629B1d974a3f28fF6E2",
        "new": "0x78beda3a06443f51718d746aDe95b5fAc094633E"
    },
    "WBERA-WETH": {
        "old": "0x79fb77363bb12464ca735b0186b4bd7131089a96",
        "new": "0x0dF14916796854d899576CBde69a35bAFb923c22"
    }
}

def run_cast(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def wei_to_ether(wei):
    return Decimal(wei) / Decimal('1000000000000000000')

def get_total_supply(vault_address):
    try:
        result = run_cast(
            f'cast call {vault_address} "totalSupply()(uint256)" --rpc-url {RPC_URL}'
        )
        return wei_to_ether(result.split()[0])
    except Exception as e:
        print(f"Error getting total supply for {vault_address}: {e}")
        return Decimal('0')

def main():
    print("\nVault Migration Balance Comparison")
    print("-" * 100)
    print(f"{'Vault Name':<15} | {'Old Vault Balance':>15} | {'New Vault Balance':>15} | {'Difference':>15} | {'Progress':>15}")
    print("-" * 100)

    total_old = Decimal('0')
    total_new = Decimal('0')

    for name, addresses in VAULTS.items():
        old_supply = get_total_supply(addresses['old'])
        new_supply = get_total_supply(addresses['new'])
        difference = new_supply - old_supply
        
        total_funds = old_supply + new_supply
        migration_percentage = (new_supply / total_funds * 100) if total_funds > 0 else Decimal('0')

        total_old += old_supply
        total_new += new_supply

        print(f"{name:<15} | {old_supply:>15.4f} | {new_supply:>15.4f} | {difference:>15.4f} | {migration_percentage:>14.2f}%")

    print("-" * 100)
    
    # Add totals
    total_funds = total_old + total_new
    total_percentage = (total_new / total_funds * 100) if total_funds > 0 else Decimal('0')
    print(f"{'TOTALS':<15} | {total_old:>15.4f} | {total_new:>15.4f} | {total_new - total_old:>15.4f} | {total_percentage:>14.2f}%")
    print("-" * 100)

if __name__ == "__main__":
    main()
