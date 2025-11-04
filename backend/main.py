"""
AlphaTransformer main application entry
"""
import asyncio
import signal
import sys

from market.websocket_client import ws_client
from market.api_client import api_client
from utils.logger import setup_logger
from config.settings import config

# Setup logging
logger = setup_logger()


async def main():
    """Main application logic"""
    logger.info("Starting AlphaTransformer market data service")
    symbols = config.agent.symbols
    timeframes = config.agent.timeframes
    logger.info(f"Configured symbols: {symbols}")
    logger.info(f"Timeframes: {timeframes}")
    
    try:
        # Initialize historical data
        logger.info("Initializing historical data...")
        await api_client.initialize_historical_data()
        
        # Connect WebSocket
        logger.info("Connecting WebSocket...")
        if await ws_client.connect():
            # Subscribe all symbols
            await ws_client.subscribe_all()
            
            # Start message loop
            message_loop_task = asyncio.create_task(ws_client.start_message_loop())
            
            logger.info("✅ AlphaTransformer started successfully!")
            logger.info("Press Ctrl+C to stop service")
            
            # Wait for signal
            await message_loop_task
        
        else:
            logger.error("❌ WebSocket connection failed")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Received stop signal, shutting down...")
    except Exception as e:
        logger.error(f"Service runtime exception: {e}")
        sys.exit(1)
    
    finally:
        # Cleanup resources
        await ws_client.disconnect()
        await api_client.close()
        logger.info("Service stopped")


def signal_handler():
    """Signal handler"""
    logger.info("Received stop signal")
    asyncio.create_task(shutdown())


async def shutdown():
    """Graceful shutdown"""
    logger.info("Gracefully shutting down...")
    await ws_client.disconnect()
    await api_client.close()
    sys.exit(0)


if __name__ == "__main__":
    # Setup signal handling
    signal.signal(signal.SIGINT, lambda s, f: signal_handler())
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler())
    
    # Run main application
    asyncio.run(main())