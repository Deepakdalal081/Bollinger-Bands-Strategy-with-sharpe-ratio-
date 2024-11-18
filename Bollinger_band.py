import pandas as pd 
import numpy as np 
import yfinance as yf 
from datetime import datetime 
import matplotlib.pyplot as plt 

# Data preparation
start_date = datetime.strptime("2024 10 10 9:15", "%Y %m %d %H:%M")
end_date = datetime.strptime("2024 11 10 3:35", "%Y %m %d %H:%M")

data = yf.download("TCS.NS", start=start_date, end=end_date, interval="15m")

# Technical indicators
data["Close"] = data["Close"].dropna()
data["MA_21"] = data["Close"].rolling(window=21, center=False).mean()
data["Sd"] = data["Close"].rolling(window=21, center=False).std()
data = data.dropna()

# Bollinger Bands
data["Upper_band"] = data["MA_21"] + 2 * data["Sd"]
data["Lower_band"] = data["MA_21"] - 2 * data["Sd"]
data["Pre_Close"] = data["Close"].shift(-1)
data["pre_Upper_band"] = data["Upper_band"].shift(-1)
data["Pre_Lower_band"] = data["Lower_band"].shift(-1)

# Signal generation
data["Sell_Signal"] = np.where(
    (data["Pre_Close"] > data["Upper_band"]) & 
    (data["Pre_Close"] < data["pre_Upper_band"]), 
    -1, 0
)
data["Sell_Exit"] = np.where(data["Close"] < data["MA_21"], 1, 0)

# Initialize tracking variables
positions = []
current_position = []
entry_price = None
trades = []
trade_returns = []

# Track positions and store closing prices
for i in range(len(data)):
    if data["Sell_Signal"].iloc[i] == -1 and entry_price is None:
        # New short position
        entry_price = data["Close"].iloc[i]
        current_position = [{
            "timestamp": data.index[i],
            "price": data["Close"].iloc[i],
            "type": "entry"
        }]
        
    elif entry_price is not None:
        # Add tracking point
        current_position.append({
            "timestamp": data.index[i],
            "price": data["Close"].iloc[i],
            "type": "tracking"
        })
        
        # Check for exit signal
        if data["Sell_Exit"].iloc[i] == 1 or data["Close"].iloc[i] >= entry_price * 1.01 :
            # Exit Position 
            current_position.append({
                "timestamp": data.index[i],
                "price": data["Close"].iloc[i],
                "type": "exit"
            })
            
            # Calculate trade result 
            exit_price = data["Close"].iloc[i]  
            trade_return = (entry_price - exit_price) / entry_price  # For short position
            
            # Store trade information
            trades.append({
                "entry_time": current_position[0]["timestamp"],
                "entry_price": entry_price,
                "exit_time": data.index[i],
                "exit_price": exit_price,
                "return": trade_return
            })
            
            # Reset tracking variables
            positions.extend(current_position)
            current_position = []
            entry_price = None
            trade_returns.append(trade_return)

# Convert to DataFrame for analysis
trades_df = pd.DataFrame(trades)
print(trades_df)
print("\nTrade Summary:")
print(f"Number of trades: {len(trades_df)}")
print(f"Average return: {trades_df['return'].mean():.2%}")
print(f"Total return: {sum(trade_returns):.2%}")
print(f"Win rate: {(trades_df['return'] > 0).mean():.2%}")

sd_of_return = np.std(trades_df["return"])
#print(sd_of_return)

# Sharpe Ratio of strategy 

# sharpe_ratio = (Average_return - Risk_free_return)/standard deviation of the return 

sharpe_ratio = (trades_df["return"].mean() - 0 )/ sd_of_return

print(sharpe_ratio)



if len(trades_df) > 0:
    
    # Plot results
    plt.figure(figsize=(15, 10))
    
    # Price and signals plot
    plt.subplot(2, 1, 1)
    plt.plot(data.index, data["Close"], label="Close Price", alpha=0.7)
    plt.plot(data.index, data["MA_21"], label="21 MA", alpha=0.7)
    plt.plot(data.index, data["Upper_band"], label="Upper Band", alpha=0.7)
    plt.plot(data.index, data["Lower_band"], label="Lower Band", alpha=0.7)
    
    # Plot entry and exit points
    for trade in trades:
        plt.scatter(trade["entry_time"], trade["entry_price"], 
                   color='red', marker='v', s=100)
        plt.scatter(trade["exit_time"], trade["exit_price"], 
                   color='green', marker='^', s=100)
    
    plt.title("TCS Price with Trading Signals")
    plt.legend()
    
    # Returns plot
    plt.subplot(2, 1, 2)
    cumulative_returns = np.cumprod(1 + trades_df["return"]) - 1
    plt.plot(trades_df.index, cumulative_returns)
    plt.title("Cumulative Strategy Returns")
    plt.xlabel("Trade Number")
    plt.ylabel("Return")
    
    plt.tight_layout()
    plt.show()
else:
    print("No trades were executed during this period.")

# Optional: Save trade data