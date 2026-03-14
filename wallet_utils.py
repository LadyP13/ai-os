"""
Wallet utilities for checking Solana balance
"""

import os
from solana.rpc.api import Client
from solders.pubkey import Pubkey

def check_wallet_balance(wallet_address):
    """
    Check Solana wallet balance
    Returns dict with SOL and total balance info
    """
    try:
        # Connect to Solana mainnet
        client = Client("https://api.mainnet-beta.solana.com")
        
        # Convert address string to Pubkey
        pubkey = Pubkey.from_string(wallet_address)
        
        # Get balance (in lamports - smallest unit)
        response = client.get_balance(pubkey)
        lamports = response.value
        
        # Convert lamports to SOL (1 SOL = 1,000,000,000 lamports)
        sol_balance = lamports / 1_000_000_000
        
        return {
            'success': True,
            'sol_balance': sol_balance,
            'lamports': lamports,
            'wallet': wallet_address
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'wallet': wallet_address
        }

def format_balance_message(balance_data):
    """Format balance data into readable message"""
    if not balance_data['success']:
        return f"❌ Error checking balance: {balance_data['error']}"
    
    sol = balance_data['sol_balance']
    
    # Estimate USD value (rough - actual would need price API)
    # For now just show SOL balance
    message = f"""💰 Wallet Balance:
Address: {balance_data['wallet'][:8]}...{balance_data['wallet'][-8:]}
SOL: {sol:.4f}
Lamports: {balance_data['lamports']:,}"""
    
    return message

if __name__ == "__main__":
    # Test it
    from dotenv import load_dotenv
    load_dotenv('config/.env')
    
    wallet = os.getenv('WALLET_ADDRESS')
    balance = check_wallet_balance(wallet)
    print(format_balance_message(balance))
