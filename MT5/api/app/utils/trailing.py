import logging
import traceback
import pandas as pd
from app.services.trade import trade_service
from app.utils import helpers
from app.db.crud import get_trade_by_ticket, mutate_trade
from app.db.database import SessionLocal
from app.utils.constants import TRAILING_STOP_STEPS

logger = logging.getLogger(__name__)
EPSILON = 1e-4

def trailing_stop_handler():
    """
    Scans open positions and applies trailing stop updates based on the predefined steps.
    """
    try:
        positions = trade_service.get_positions()
        if not positions:
            return

        df = pd.DataFrame(positions)
        with SessionLocal() as session:
            for _, pos in df.iterrows():
                # Try to find corresponding trade in our DB for capital/size info
                trade = get_trade_by_ticket(session, str(pos['ticket']))
                if not trade:
                    continue

                for step in TRAILING_STOP_STEPS:
                    trigger_pnl = trade.capital * step['trigger_pnl_multiplier']
                    new_sl_pnl = trade.capital * step['new_sl_pnl_multiplier']

                    new_sl_price, _ = helpers.get_price_at_pnl(
                        desired_pnl=new_sl_pnl,
                        commission=trade.order_commission,
                        order_size_usd=trade.position_size_usd,
                        leverage=trade.leverage,
                        entry_price=pos['price_open'],
                        type=trade.type
                    )

                    if pos['profit'] >= trigger_pnl:
                        # Check if new SL is better than current SL
                        if (trade.type == 'BUY' and new_sl_price > pos['sl'] + EPSILON) or \
                           (trade.type == 'SELL' and new_sl_price < pos['sl'] - EPSILON):
                            
                            result = trade_service.modify_sl_tp(pos['ticket'], new_sl_price)
                            if result and result.retcode == 10009:
                                mutate_trade(session, trade.id, pos['price_current'], new_sl_price, None)
                                logger.info(f"Trailing stop updated for {pos['symbol']} (ticket {pos['ticket']})")
                                break
    except Exception as e:
        logger.error(f"Error in trailing_stop_handler: {e}\n{traceback.format_exc()}")
