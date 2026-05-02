from app.utils.config import accounts, Account, env
accounts['def'] = Account(env.MT5_ACCOUNT_NUMBER, env.MT5_PASSWORD)
